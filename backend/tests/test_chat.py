"""Tests for POST /v1/chat.

The harness is replaced by FakeAgentCore, so tests need no network, no AWS
account, and cost nothing. The event shapes copy a real InvokeHarness stream
captured on 2026-09-11, shortened.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.aws import get_agentcore
from app.main import app
from tests.conftest import TEST_SETTINGS
from tests.helpers import TENANT, FakeAgentCore, aws_error, parse_sse

SESSION = "s" * 40
RESULT = json.dumps(
    {
        "retrievalResults": [
            {
                "content": {"text": "Neptune costs $3.51 an hour", "type": "TEXT"},
                "metadata": {"_document_title": "README.md", "tenant_id": "dev"},
                "score": 0.61234,
            }
        ]
    }
)


def usage(inputs: int, outputs: int) -> dict[str, Any]:
    return {
        "metadata": {
            "usage": {"inputTokens": inputs, "outputTokens": outputs},
            "metrics": {"latencyMs": 900},
        }
    }


# One question, one search, one answer: two model calls.
HAPPY_EVENTS: list[dict[str, Any]] = [
    {"messageStart": {"role": "assistant"}},
    {
        "contentBlockDelta": {
            "contentBlockIndex": 1,
            "delta": {"reasoningContent": {"text": "search first"}},
        }
    },
    {"contentBlockStop": {"contentBlockIndex": 1}},
    {
        "contentBlockStart": {
            "contentBlockIndex": 2,
            "start": {"toolUse": {"toolUseId": "t1", "name": "docs___Retrieve"}},
        }
    },
    {
        "contentBlockDelta": {
            "contentBlockIndex": 2,
            "delta": {"toolUse": {"input": '{"retrievalQuery": '}},
        }
    },
    {
        "contentBlockDelta": {
            "contentBlockIndex": 2,
            "delta": {"toolUse": {"input": '{"text": "neptune"}}'}},
        }
    },
    {"contentBlockStop": {"contentBlockIndex": 2}},
    {"messageStop": {"stopReason": "tool_use"}},
    usage(300, 80),
    {"messageStart": {"role": "user"}},
    {
        "contentBlockStart": {
            "contentBlockIndex": 0,
            "start": {"toolResult": {"toolUseId": "t1", "status": "success"}},
        }
    },
    # The result arrives as pieces of one JSON string.
    {
        "contentBlockDelta": {
            "contentBlockIndex": 0,
            "delta": {"toolResult": [{"text": RESULT[:40]}]},
        }
    },
    {
        "contentBlockDelta": {
            "contentBlockIndex": 0,
            "delta": {"toolResult": [{"text": RESULT[40:]}]},
        }
    },
    {"contentBlockStop": {"contentBlockIndex": 0}},
    {"messageStop": {"stopReason": "tool_result"}},
    {"messageStart": {"role": "assistant"}},
    {"contentBlockDelta": {"contentBlockIndex": 1, "delta": {"text": "Cost"}}},
    {"contentBlockDelta": {"contentBlockIndex": 1, "delta": {"text": " [1]"}}},
    {"contentBlockStop": {"contentBlockIndex": 1}},
    {"messageStop": {"stopReason": "end_turn"}},
    usage(3000, 200),
]


def client_using(fake: FakeAgentCore) -> TestClient:
    app.dependency_overrides[get_agentcore] = lambda: fake
    return TestClient(app)


def ask(
    fake: FakeAgentCore, body: dict[str, Any] | None = None, headers: dict[str, str] = TENANT
) -> Any:
    return client_using(fake).post("/v1/chat", headers=headers, json=body or {"message": "why?"})


# ---------- happy path ----------


def test_streams_session_tool_sources_answer_usage_done() -> None:
    response = ask(FakeAgentCore(stream=HAPPY_EVENTS), {"message": "why?", "session_id": SESSION})

    assert response.status_code == 200
    events = parse_sse(response.text)
    assert [name for name, _ in events] == [
        "session",
        "tool",
        "sources",
        "delta",
        "delta",
        "usage",
        "done",
    ]
    data = [json.loads(d) if name != "done" else d for name, d in events]
    assert data[0] == {"session_id": SESSION}
    assert data[1] == {"name": "docs___Retrieve", "input": {"retrievalQuery": {"text": "neptune"}}}
    assert data[2] == [
        {"n": 1, "title": "README.md", "score": 0.612, "excerpt": "Neptune costs $3.51 an hour"}
    ]
    assert data[3:5] == ["Cost", " [1]"]
    assert data[5] == {"input_tokens": 3300, "output_tokens": 280, "model_calls": 2}


def test_sends_the_harness_session_tenant_and_message() -> None:
    fake = FakeAgentCore(stream=HAPPY_EVENTS)

    ask(fake, {"message": "why?", "session_id": SESSION})

    assert fake.calls == [
        (
            "invoke_harness",
            {
                "harnessArn": TEST_SETTINGS.harness_arn,
                "runtimeSessionId": SESSION,
                "actorId": "dev",
                "messages": [{"role": "user", "content": [{"text": "why?"}]}],
            },
        )
    ]


def test_new_conversation_gets_a_fresh_session_id() -> None:
    fake = FakeAgentCore(stream=HAPPY_EVENTS)

    events = parse_sse(ask(fake).text)

    session_id = json.loads(events[0][1])["session_id"]
    assert len(session_id) == 36
    assert fake.calls[0][1]["runtimeSessionId"] == session_id


def test_a_tool_result_that_is_not_a_search_gives_no_sources() -> None:
    stream: list[dict[str, Any]] = [
        {
            "contentBlockStart": {
                "contentBlockIndex": 0,
                "start": {"toolResult": {"toolUseId": "t", "status": "success"}},
            }
        },
        {
            "contentBlockDelta": {
                "contentBlockIndex": 0,
                "delta": {"toolResult": [{"text": "not json"}]},
            }
        },
        {"contentBlockStop": {"contentBlockIndex": 0}},
    ]

    events = parse_sse(ask(FakeAgentCore(stream=stream)).text)

    assert "sources" not in [name for name, _ in events]


# ---------- rejected before the harness is called ----------


@pytest.mark.parametrize(
    "headers", [{}, {"X-Tenant-Id": "has space"}, {"X-Tenant-Id": "_starts-badly"}]
)
def test_bad_tenant_header_is_400_and_costs_nothing(headers: dict[str, str]) -> None:
    fake = FakeAgentCore(stream=HAPPY_EVENTS)

    response = ask(fake, headers=headers)

    assert response.status_code == 400
    assert fake.calls == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"message": ""},
        {"message": "hi", "session_id": "too-short"},
        {"message": "hi", "session_id": "has spaces " * 4},
    ],
    ids=["no-message", "empty-message", "short-session", "bad-session-chars"],
)
def test_invalid_request_is_422_and_costs_nothing(body: dict[str, Any]) -> None:
    fake = FakeAgentCore(stream=HAPPY_EVENTS)

    response = client_using(fake).post("/v1/chat", headers=TENANT, json=body)

    assert response.status_code == 422
    assert fake.calls == []


# ---------- the harness refuses before streaming starts ----------


def test_throttling_is_503_with_retry_after() -> None:
    response = ask(FakeAgentCore(error=aws_error("ThrottlingException")))

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"


def test_other_error_is_502_without_leaking_details() -> None:
    response = ask(FakeAgentCore(error=aws_error("AccessDeniedException")))

    assert response.status_code == 502
    assert "AccessDenied" not in response.text


# ---------- the harness fails after streaming started ----------


def test_error_event_in_the_stream_becomes_error_without_details() -> None:
    stream: list[dict[str, Any]] = [
        {"contentBlockDelta": {"contentBlockIndex": 1, "delta": {"text": "Co"}}},
        {"runtimeClientError": {"message": "secret internals"}},
    ]

    response = ask(FakeAgentCore(stream=stream))

    events = parse_sse(response.text)
    assert [name for name, _ in events] == ["session", "delta", "error"]
    assert "secret internals" not in response.text


def test_broken_connection_mid_stream_becomes_error_event() -> None:
    def breaks_after_one_piece() -> Iterator[dict[str, Any]]:
        yield {"contentBlockDelta": {"contentBlockIndex": 1, "delta": {"text": "Co"}}}
        raise aws_error("InternalServerException")

    events = parse_sse(ask(FakeAgentCore(stream=breaks_after_one_piece())).text)

    assert [name for name, _ in events] == ["session", "delta", "error"]
