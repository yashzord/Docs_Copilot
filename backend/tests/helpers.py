"""Small helpers shared by the test files."""

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

import httpx2
from botocore.exceptions import ClientError


def aws_error(code: str) -> ClientError:
    """The exception boto3 raises when AWS answers with an error."""
    return ClientError({"Error": {"Code": code, "Message": "test"}}, "Test")


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


class FakeAgentCore:
    """Stands in for the bedrock-agentcore client (Memory reads).

    Records calls, returns canned answers. Injected through FastAPI's dependency overrides.
    https://fastapi.tiangolo.com/advanced/testing-dependencies/
    """

    def __init__(
        self,
        sessions: Iterable[dict[str, Any]] = (),
        event_pages: Iterable[list[dict[str, Any]]] = (
            [{"eventId": "e0", "eventTimestamp": datetime(2026, 9, 11, tzinfo=UTC), "payload": []}],
        ),
        error: ClientError | None = None,
        empty_sessions: Iterable[str] = (),
    ) -> None:
        self.sessions = list(sessions)
        self.event_pages = list(event_pages)
        # Conversations whose events were deleted: list_events returns nothing for them.
        self.empty_sessions = set(empty_sessions)
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _record(self, name: str, kwargs: dict[str, Any]) -> None:
        self.calls.append((name, kwargs))
        if self.error is not None:
            raise self.error

    def list_sessions(self, **kwargs: Any) -> dict[str, Any]:
        self._record("list_sessions", kwargs)
        return {"sessionSummaries": self.sessions}

    def list_events(self, **kwargs: Any) -> dict[str, Any]:
        self._record("list_events", kwargs)
        if kwargs.get("sessionId") in self.empty_sessions:
            return {"events": []}
        page = int(kwargs.get("nextToken", 0))
        response: dict[str, Any] = {"events": self.event_pages[page]}
        if page + 1 < len(self.event_pages):
            response["nextToken"] = str(page + 1)
        return response


def sse_body(events: Iterable[dict[str, Any]]) -> bytes:
    """What Runtime sends for an agent that yielded these JSON events: one SSE line each,
    the JSON text encoded once more as a JSON string (that is what Runtime does)."""
    return "".join(f"data: {json.dumps(json.dumps(e))}\n\n" for e in events).encode()


class FakeRuntime:
    """Stands in for AgentCore Runtime behind an httpx2 client: records the request,
    answers with a canned status and body. Injected as the chat route's HTTP client."""

    def __init__(
        self, events: Iterable[dict[str, Any]] = (), status: int = 200, body: bytes | None = None
    ) -> None:
        self.body = sse_body(events) if body is None else body
        self.status = status
        self.requests: list[httpx2.Request] = []

    def client(self) -> httpx2.Client:
        def handle(request: httpx2.Request) -> httpx2.Response:
            self.requests.append(request)
            return httpx2.Response(
                self.status, content=self.body, headers={"content-type": "text/event-stream"}
            )

        return httpx2.Client(transport=httpx2.MockTransport(handle))
