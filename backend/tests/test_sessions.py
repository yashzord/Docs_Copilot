"""Tests for /v1/sessions: the chat sidebar, read from AgentCore Memory.

Memory event shapes copy what the harness wrote for a real turn on 2026-09-11.
"""

import json
from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient

from app.aws import get_agentcore
from app.main import app
from tests.conftest import TEST_SETTINGS
from tests.helpers import TENANT, FakeAgentCore, aws_error

SESSION = "s" * 40


def at(second: int) -> datetime:
    return datetime(2026, 9, 11, 0, 0, second, tzinfo=UTC)


def memory_event(second: int, role: str, content: list[dict[str, Any]]) -> dict[str, Any]:
    """A "conversational" event as the harness writes it: the message as JSON text."""
    text = json.dumps({"message": {"role": role, "content": content}, "message_id": second})
    return {
        "eventId": f"e{second}",
        "eventTimestamp": at(second),
        "payload": [{"conversational": {"role": role.upper(), "content": {"text": text}}}],
    }


BLOB = {"eventId": "b", "eventTimestamp": at(0), "payload": [{"blob": '{"agent_id": "default"}'}]}
TURN = [
    memory_event(1, "user", [{"text": "Why was Neptune dropped?"}]),
    memory_event(
        2, "assistant", [{"reasoningContent": {}}, {"toolUse": {"name": "docs___Retrieve"}}]
    ),
    memory_event(3, "user", [{"toolResult": {"status": "success"}}]),
    memory_event(
        4, "assistant", [{"reasoningContent": {}}, {"text": "It costs $3.51 an hour [1]."}]
    ),
]


def client_using(fake: FakeAgentCore) -> TestClient:
    app.dependency_overrides[get_agentcore] = lambda: fake
    return TestClient(app)


def test_lists_this_tenants_sessions_newest_first() -> None:
    fake = FakeAgentCore(
        sessions=[
            {"sessionId": "old", "actorId": "dev", "createdAt": at(1)},
            {"sessionId": "new", "actorId": "dev", "createdAt": at(9)},
        ]
    )

    response = client_using(fake).get("/v1/sessions", headers=TENANT)

    assert response.status_code == 200
    assert [s["session_id"] for s in response.json()] == ["new", "old"]
    assert fake.calls == [
        (
            "list_sessions",
            {"memoryId": TEST_SETTINGS.memory_id, "actorId": "dev", "maxResults": 100},
        )
    ]


def test_messages_keep_only_question_and_answer_text_in_order() -> None:
    # Out of order, with a blob, on purpose.
    fake = FakeAgentCore(event_pages=[[TURN[3], BLOB, TURN[1], TURN[0], TURN[2]]])

    response = client_using(fake).get(f"/v1/sessions/{SESSION}/messages", headers=TENANT)

    assert response.status_code == 200
    assert response.json() == [
        {"role": "user", "text": "Why was Neptune dropped?"},
        {"role": "assistant", "text": "It costs $3.51 an hour [1]."},
    ]
    assert fake.calls[0][1]["actorId"] == "dev"
    assert fake.calls[0][1]["includePayloads"] is True


def test_messages_follow_every_page() -> None:
    fake = FakeAgentCore(event_pages=[[TURN[0]], [TURN[3]]])

    response = client_using(fake).get(f"/v1/sessions/{SESSION}/messages", headers=TENANT)

    assert [m["role"] for m in response.json()] == ["user", "assistant"]
    assert len(fake.calls) == 2


def test_malformed_memory_text_is_skipped() -> None:
    broken = {
        "eventId": "x",
        "eventTimestamp": at(5),
        "payload": [{"conversational": {"role": "USER", "content": {"text": "not json"}}}],
    }
    fake = FakeAgentCore(event_pages=[[TURN[0], broken]])

    response = client_using(fake).get(f"/v1/sessions/{SESSION}/messages", headers=TENANT)

    assert response.json() == [{"role": "user", "text": "Why was Neptune dropped?"}]


def test_malformed_session_id_is_422_and_costs_nothing() -> None:
    fake = FakeAgentCore()

    response = client_using(fake).get("/v1/sessions/short/messages", headers=TENANT)

    assert response.status_code == 422
    assert fake.calls == []


def test_memory_error_is_502() -> None:
    response = client_using(FakeAgentCore(error=aws_error("AccessDeniedException"))).get(
        "/v1/sessions", headers=TENANT
    )

    assert response.status_code == 502
