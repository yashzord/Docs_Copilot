"""Tests for POST /v1/chat.

Bedrock is replaced by FakeBedrock, so tests need no network, no AWS account,
and cost nothing. Each test covers one behavior: the happy path, or one way
things go wrong.
"""

import json
from collections.abc import Iterable, Iterator
from typing import Any

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from app.llm import get_bedrock_client
from app.main import app
from app.settings import Settings, get_settings

TENANT = {"X-Tenant-Id": "dev"}
ONE_QUESTION = {"messages": [{"role": "user", "content": "hi"}]}

# The event sequence Bedrock sends for a two-piece answer.
# Shapes from the ConverseStream response syntax:
# https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse_stream.html
HAPPY_EVENTS: list[dict[str, Any]] = [
    {"messageStart": {"role": "assistant"}},
    {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": "Hel"}}},
    {"contentBlockDelta": {"contentBlockIndex": 0, "delta": {"text": "lo"}}},
    {"contentBlockStop": {"contentBlockIndex": 0}},
    {"messageStop": {"stopReason": "end_turn"}},
    {
        "metadata": {
            "usage": {"inputTokens": 5, "outputTokens": 2, "totalTokens": 7},
            "metrics": {"latencyMs": 120},
        }
    },
]


def aws_error(code: str) -> ClientError:
    """The exception boto3 raises when AWS answers with an error."""
    return ClientError({"Error": {"Code": code, "Message": "test"}}, "ConverseStream")


class FakeBedrock:
    """Stands in for the boto3 client.

    botocore's Stubber would be the usual tool, but it cannot fake an event
    stream (it rejects a plain list), so tests inject this object through
    FastAPI's dependency overrides instead.
    https://fastapi.tiangolo.com/advanced/testing-dependencies/
    """

    def __init__(
        self, stream: Iterable[dict[str, Any]] = (), error: ClientError | None = None
    ) -> None:
        self.stream = stream
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def converse_stream(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return {"stream": self.stream}


@pytest.fixture(autouse=True)
def _test_settings() -> Iterator[None]:
    # _env_file=None: ignore backend/.env, so tests behave the same on every machine.
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, bedrock_synth_model_id="test-model"
    )
    yield
    app.dependency_overrides.clear()


def client_using(fake: FakeBedrock) -> TestClient:
    app.dependency_overrides[get_bedrock_client] = lambda: fake
    return TestClient(app)


def parse_sse(body: str) -> list[tuple[str, str]]:
    """Turn an SSE body into (event, data) pairs. Comment lines (keep-alive pings) are skipped."""
    events = []
    for block in body.strip().split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if line.startswith(":"):
                continue
            key, _, value = line.partition(":")
            fields[key] = value.removeprefix(" ")
        if fields:
            events.append((fields.get("event", "message"), fields.get("data", "")))
    return events


# ---------- happy path ----------


def test_streams_text_then_usage_then_done() -> None:
    fake = FakeBedrock(stream=HAPPY_EVENTS)

    response = client_using(fake).post("/v1/chat", headers=TENANT, json=ONE_QUESTION)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    assert events[:2] == [("delta", '"Hel"'), ("delta", '"lo"')]
    assert events[2][0] == "usage"
    assert json.loads(events[2][1]) == {"input_tokens": 5, "output_tokens": 2, "latency_ms": 120}
    assert events[3] == ("done", "[DONE]")


def test_sends_bedrock_the_converse_request_shape() -> None:
    fake = FakeBedrock(stream=HAPPY_EVENTS)

    client_using(fake).post("/v1/chat", headers=TENANT, json=ONE_QUESTION)

    assert fake.calls == [
        {
            "modelId": "test-model",
            "messages": [{"role": "user", "content": [{"text": "hi"}]}],
            "inferenceConfig": {"maxTokens": 1024},
        }
    ]


# ---------- rejected before Bedrock is called ----------


@pytest.mark.parametrize("headers", [{}, {"X-Tenant-Id": "has space"}, {"X-Tenant-Id": "a" * 65}])
def test_bad_tenant_header_is_400_and_costs_nothing(headers: dict[str, str]) -> None:
    fake = FakeBedrock(stream=HAPPY_EVENTS)

    response = client_using(fake).post("/v1/chat", headers=headers, json=ONE_QUESTION)

    assert response.status_code == 400
    assert fake.calls == []


@pytest.mark.parametrize(
    "messages",
    [
        [],
        [{"role": "assistant", "content": "hi"}],
        [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        [{"role": "user", "content": ""}],
        [{"role": "system", "content": "hi"}],
    ],
    ids=["empty", "starts-with-assistant", "ends-with-assistant", "empty-text", "unknown-role"],
)
def test_invalid_conversation_is_422_and_costs_nothing(messages: list[dict[str, str]]) -> None:
    fake = FakeBedrock(stream=HAPPY_EVENTS)

    response = client_using(fake).post("/v1/chat", headers=TENANT, json={"messages": messages})

    assert response.status_code == 422
    assert fake.calls == []


# ---------- Bedrock refuses before streaming starts ----------


def test_throttling_is_503_with_retry_after() -> None:
    fake = FakeBedrock(error=aws_error("ThrottlingException"))

    response = client_using(fake).post("/v1/chat", headers=TENANT, json=ONE_QUESTION)

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"


def test_other_bedrock_error_is_502_without_leaking_details() -> None:
    fake = FakeBedrock(error=aws_error("AccessDeniedException"))

    response = client_using(fake).post("/v1/chat", headers=TENANT, json=ONE_QUESTION)

    assert response.status_code == 502
    assert "AccessDenied" not in response.text


# ---------- Bedrock fails after streaming started ----------


def test_error_mid_stream_becomes_error_event() -> None:
    def breaks_after_one_piece() -> Iterator[dict[str, Any]]:
        yield HAPPY_EVENTS[1]
        raise aws_error("modelStreamErrorException")

    fake = FakeBedrock(stream=breaks_after_one_piece())

    response = client_using(fake).post("/v1/chat", headers=TENANT, json=ONE_QUESTION)

    assert response.status_code == 200
    events = parse_sse(response.text)
    assert events[0] == ("delta", '"Hel"')
    assert events[1][0] == "error"
    assert ("done", "[DONE]") not in events
