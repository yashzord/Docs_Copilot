"""Small helpers shared by the test files."""

from collections.abc import Iterable
from typing import Any

from botocore.exceptions import ClientError

TENANT = {"X-Tenant-Id": "dev"}


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
    """Stands in for the bedrock-agentcore client: records calls, returns canned answers.

    botocore's Stubber cannot fake an event stream (it rejects a plain list), so
    tests inject this object through FastAPI's dependency overrides instead.
    https://fastapi.tiangolo.com/advanced/testing-dependencies/
    """

    def __init__(
        self,
        stream: Iterable[dict[str, Any]] = (),
        sessions: Iterable[dict[str, Any]] = (),
        event_pages: Iterable[list[dict[str, Any]]] = ([],),
        error: ClientError | None = None,
    ) -> None:
        self.stream = stream
        self.sessions = list(sessions)
        self.event_pages = list(event_pages)
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _record(self, name: str, kwargs: dict[str, Any]) -> None:
        self.calls.append((name, kwargs))
        if self.error is not None:
            raise self.error

    def invoke_harness(self, **kwargs: Any) -> dict[str, Any]:
        self._record("invoke_harness", kwargs)
        return {"stream": self.stream}

    def list_sessions(self, **kwargs: Any) -> dict[str, Any]:
        self._record("list_sessions", kwargs)
        return {"sessionSummaries": self.sessions}

    def list_events(self, **kwargs: Any) -> dict[str, Any]:
        self._record("list_events", kwargs)
        page = int(kwargs.get("nextToken", 0))
        response: dict[str, Any] = {"events": self.event_pages[page]}
        if page + 1 < len(self.event_pages):
            response["nextToken"] = str(page + 1)
        return response
