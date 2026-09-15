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
from tests.helpers import FakeAgentCore, aws_error

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


def test_lists_this_users_sessions_newest_first() -> None:
    fake = FakeAgentCore(
        sessions=[
            {"sessionId": "old", "actorId": "user-a", "createdAt": at(1)},
            {"sessionId": "new", "actorId": "user-a", "createdAt": at(9)},
        ]
    )

    response = client_using(fake).get("/v1/sessions")

    assert response.status_code == 200
    assert [s["session_id"] for s in response.json()] == ["new", "old"]
    assert response.json()[0]["title"] == "Untitled chat"
    assert fake.calls[0] == (
        "list_sessions",
        {"memoryId": TEST_SETTINGS.memory_id, "actorId": "user-a", "maxResults": 100},
    )


def test_conversations_with_no_events_are_hidden() -> None:
    # AgentCore can delete a conversation's events but not the conversation itself.
    fake = FakeAgentCore(
        sessions=[
            {"sessionId": "wiped", "actorId": "user-a", "createdAt": at(1)},
            {"sessionId": "real", "actorId": "user-a", "createdAt": at(2)},
        ],
        empty_sessions=["wiped"],
    )

    response = client_using(fake).get("/v1/sessions")

    assert [s["session_id"] for s in response.json()] == ["real"]
    assert (
        "list_events",
        {
            "memoryId": TEST_SETTINGS.memory_id,
            "sessionId": "wiped",
            "actorId": "user-a",
            "includePayloads": True,
            "maxResults": 100,
        },
    ) in fake.calls


def test_title_is_the_first_question() -> None:
    # Out of order on purpose: the earliest user message wins.
    fake = FakeAgentCore(
        sessions=[{"sessionId": SESSION, "actorId": "user-a", "createdAt": at(1)}],
        event_pages=[[TURN[3], BLOB, TURN[1], TURN[0], TURN[2]]],
    )

    response = client_using(fake).get("/v1/sessions")

    assert response.json()[0]["title"] == "Why was Neptune dropped?"


def test_long_title_is_shortened() -> None:
    question = "How does the Gateway relate to Memory and the Harness in this whole project?"
    fake = FakeAgentCore(
        sessions=[{"sessionId": SESSION, "actorId": "user-a", "createdAt": at(1)}],
        event_pages=[[memory_event(1, "user", [{"text": question}])]],
    )

    title = client_using(fake).get("/v1/sessions").json()[0]["title"]

    assert len(title) <= 60
    assert title.endswith("...")
    assert question.startswith(title[:-3])


def test_messages_keep_only_question_and_answer_text_in_order() -> None:
    # Out of order, with a blob, on purpose.
    fake = FakeAgentCore(event_pages=[[TURN[3], BLOB, TURN[1], TURN[0], TURN[2]]])

    response = client_using(fake).get(f"/v1/sessions/{SESSION}/messages")

    assert response.status_code == 200
    assert response.json() == [
        {"role": "user", "text": "Why was Neptune dropped?"},
        {"role": "assistant", "text": "It costs $3.51 an hour [1]."},
    ]
    assert fake.calls[0][1]["actorId"] == "user-a"
    assert fake.calls[0][1]["includePayloads"] is True


def test_messages_follow_every_page() -> None:
    fake = FakeAgentCore(event_pages=[[TURN[0]], [TURN[3]]])

    response = client_using(fake).get(f"/v1/sessions/{SESSION}/messages")

    assert [m["role"] for m in response.json()] == ["user", "assistant"]
    assert len(fake.calls) == 2


def test_malformed_memory_text_is_skipped() -> None:
    broken = {
        "eventId": "x",
        "eventTimestamp": at(5),
        "payload": [{"conversational": {"role": "USER", "content": {"text": "not json"}}}],
    }
    fake = FakeAgentCore(event_pages=[[TURN[0], broken]])

    response = client_using(fake).get(f"/v1/sessions/{SESSION}/messages")

    assert response.json() == [{"role": "user", "text": "Why was Neptune dropped?"}]


def test_malformed_session_id_is_422_and_costs_nothing() -> None:
    fake = FakeAgentCore()

    response = client_using(fake).get("/v1/sessions/short/messages")

    assert response.status_code == 422
    assert fake.calls == []


def test_memory_error_is_502() -> None:
    response = client_using(FakeAgentCore(error=aws_error("AccessDeniedException"))).get(
        "/v1/sessions"
    )

    assert response.status_code == 502
