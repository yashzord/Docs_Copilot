"""Tests for POST /v1/chat.

AgentCore Runtime is replaced by FakeRuntime (an in-memory HTTP transport), so
tests need no network, no AWS account, and cost nothing. The event shapes copy
what agent/src/main.py yields, captured on 2026-09-15.
"""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.auth import get_user
from app.chat import get_http
from app.main import app
from tests.conftest import TEST_SETTINGS
from tests.helpers import FakeRuntime, parse_sse

SESSION = "s" * 40
RESULT = json.dumps(
    {
        "retrievalResults": [
            {
                "content": {"text": "Neptune costs $3.51 an hour", "type": "TEXT"},
                "metadata": {"_document_title": "README.md", "user-a": "owner"},
                "score": 0.61234,
            }
        ]
    }
)

# One question, one search, one answer: two model calls.
HAPPY_EVENTS: list[dict[str, Any]] = [
    {"type": "text", "text": ""},
    {"type": "tool", "name": "docs___Retrieve", "input": {"retrievalQuery": {"text": "neptune"}}},
    {"type": "tool_result", "text": RESULT},
    {"type": "text", "text": "Cost"},
    {"type": "text", "text": " [1]"},
    {"type": "usage", "input_tokens": 3300, "output_tokens": 280, "model_calls": 2},
]


def client_using(fake: FakeRuntime) -> TestClient:
    app.dependency_overrides[get_http] = fake.client
    return TestClient(app)


def ask(fake: FakeRuntime, body: dict[str, Any] | None = None) -> Any:
    return client_using(fake).post("/v1/chat", json=body or {"message": "why?"})


# ---------- happy path ----------


def test_streams_session_tool_sources_answer_usage_done() -> None:
    response = ask(FakeRuntime(HAPPY_EVENTS), {"message": "why?", "session_id": SESSION})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert parse_sse(response.text) == [
        ("session", json.dumps({"session_id": SESSION})),
        (
            "tool",
            json.dumps(
                {"name": "docs___Retrieve", "input": {"retrievalQuery": {"text": "neptune"}}}
            ),
        ),
        (
            "sources",
            json.dumps(
                [
                    {
                        "n": 1,
                        "title": "README.md",
                        "score": 0.612,
                        "excerpt": "Neptune costs $3.51 an hour",
                    }
                ]
            ),
        ),
        ("delta", json.dumps("Cost")),
        ("delta", json.dumps(" [1]")),
        ("usage", json.dumps({"input_tokens": 3300, "output_tokens": 280, "model_calls": 2})),
        ("done", "[DONE]"),
    ]


def test_calls_runtime_with_the_users_token_session_and_message() -> None:
    fake = FakeRuntime(HAPPY_EVENTS)

    ask(fake, {"message": "why?", "session_id": SESSION})

    [request] = fake.requests
    assert request.method == "POST"
    assert str(request.url) == (
        "https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/"
        "arn%3Aaws%3Abedrock-agentcore%3Aus-west-2%3A000000000000%3Aruntime%2Ftest"
        "/invocations?qualifier=DEFAULT"
    )
    assert request.headers["authorization"] == "Bearer test-token"
    assert request.headers["x-amzn-bedrock-agentcore-runtime-session-id"] == SESSION
    assert json.loads(request.content) == {"message": "why?"}
    assert TEST_SETTINGS.agent_runtime_arn in str(request.url).replace("%3A", ":").replace(
        "%2F", "/"
    )


def test_new_conversation_gets_a_fresh_session_id() -> None:
    fake = FakeRuntime(HAPPY_EVENTS)

    events = parse_sse(ask(fake).text)

    session_id = json.loads(events[0][1])["session_id"]
    assert len(session_id) == 36  # a UUID
    assert fake.requests[0].headers["x-amzn-bedrock-agentcore-runtime-session-id"] == session_id


def test_a_tool_result_that_is_not_a_search_gives_no_sources() -> None:
    events: list[dict[str, Any]] = [
        {
            "type": "tool",
            "name": "browser",
            "input": {"browser_input": {"action": {"type": "navigate"}}},
        },
        {"type": "tool_result", "text": "Page text here"},
        {"type": "text", "text": "Done."},
        {"type": "usage", "input_tokens": 10, "output_tokens": 2, "model_calls": 2},
    ]

    kinds = [event for event, _ in parse_sse(ask(FakeRuntime(events)).text)]

    assert kinds == ["session", "tool", "delta", "usage", "done"]


# ---------- refusals, before any token is spent ----------


@pytest.mark.parametrize(
    "headers", [{}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer not.a.jwt"}]
)
def test_no_valid_token_is_401_and_costs_nothing(headers: dict[str, str]) -> None:
    fake = FakeRuntime(HAPPY_EVENTS)
    client = client_using(fake)
    del app.dependency_overrides[get_user]  # the real check, not the test user

    response = client.post("/v1/chat", headers=headers, json={"message": "why?"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert fake.requests == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"message": ""},
        {"message": "x" * 20_001},
        {"message": "hi", "session_id": "short"},
        {"message": "hi", "session_id": "-starts-badly" + "x" * 40},
    ],
)
def test_invalid_request_is_422_and_costs_nothing(body: dict[str, Any]) -> None:
    fake = FakeRuntime(HAPPY_EVENTS)

    response = client_using(fake).post("/v1/chat", json=body)

    assert response.status_code == 422
    assert fake.requests == []


# ---------- the agent refuses or fails ----------


def test_runtime_401_becomes_401() -> None:
    response = ask(FakeRuntime(status=401, body=b"{}"))

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("status", [429, 503])
def test_busy_runtime_is_503_with_retry_after(status: int) -> None:
    response = ask(FakeRuntime(status=status, body=b"{}"))

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"


def test_other_runtime_error_is_502_without_leaking_details() -> None:
    response = ask(FakeRuntime(status=500, body=b'{"message": "internal secret"}'))

    assert response.status_code == 502
    assert "secret" not in response.text


def test_error_event_in_the_stream_becomes_error_without_details() -> None:
    events = [
        {"type": "text", "text": "Nep"},
        {"type": "error", "message": "MCPClientInitializationError: something internal"},
        {"type": "text", "text": "never sent"},
    ]

    response = ask(FakeRuntime(events))

    assert response.status_code == 200
    assert parse_sse(response.text)[1:] == [
        ("delta", json.dumps("Nep")),
        ("error", json.dumps({"message": "The assistant stopped unexpectedly."})),
    ]
    assert "internal" not in response.text


def test_broken_stream_mid_answer_becomes_error_event() -> None:
    # A truncated line: not JSON. The stream must end with an error, not crash.
    broken = b'data: "{\\"type\\": \\"text\\", \\"text\\": \\"Nep\\"}"\n\ndata: {"type": "text"'

    response = ask(FakeRuntime(body=broken))

    assert response.status_code == 200
    events = parse_sse(response.text)
    assert ("delta", json.dumps("Nep")) in events
    assert events[-1] == ("error", json.dumps({"message": "The assistant stopped unexpectedly."}))
