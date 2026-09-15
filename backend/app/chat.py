"""POST /v1/chat: one question in, the agent's answer out as Server-Sent Events.

The agent is our Strands agent on AgentCore Runtime (agent/src/main.py, lesson
17). It keeps the conversation in AgentCore Memory, so the browser sends only
the new message and a session id, never the history.

The call to the agent carries the signed-in user's own Cognito token. Runtime
checks it (its JWT authorizer), and the agent passes it on to the Gateway, so
every hop knows who is asking (lesson 22). AWS SDKs cannot send a bearer token
to Runtime, so this is a plain HTTPS request with a streaming HTTP client.

Wire format, in order:

    event: session  data: {"session_id": "..."}                       always first
    event: tool     data: {"name": "docs___Retrieve", "input": {...}}  the agent searched
    event: sources  data: [{"n": 1, "title": "README.md", "score": 0.61, "excerpt": "..."}]
    event: delta    data: "Nep"                                        answer text, piece by piece
    event: usage    data: {"input_tokens": 3561, "output_tokens": 363, "model_calls": 2}
    event: done     data: [DONE]

or, if the agent fails after streaming began:

    event: error    data: {"message": "..."}
"""

import json
import logging
import uuid
from collections.abc import Iterable, Iterator
from functools import lru_cache
from typing import Annotated, Any
from urllib.parse import quote

import httpx2
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field

from app.auth import User, get_user, get_user_id
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Runtime accepts 33 to 100 letters, digits, dashes or underscores, starting
# with a letter or digit. A UUID is 36 characters.
SESSION_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{32,99}$"
_EXCERPT_CHARS = 300


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    # Leave out to start a new conversation; the first event carries the new id.
    session_id: str | None = Field(default=None, pattern=SESSION_ID_PATTERN)


def session_id_for(request: ChatRequest) -> str:
    # FastAPI runs this once per request, so every dependency sees the same id.
    return request.session_id or str(uuid.uuid4())


@lru_cache
def get_http() -> httpx2.Client:
    # One client, shared: it keeps connections open between requests. An agent can
    # go quiet while it searches or thinks, so wait up to 5 minutes for the next byte.
    # https://www.python-httpx.org/advanced/clients/
    return httpx2.Client(timeout=httpx2.Timeout(connect=10, read=300, write=30, pool=10))


def agent_url(settings: Settings) -> str:
    # https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html
    arn = quote(settings.agent_runtime_arn, safe="")
    return (
        f"https://bedrock-agentcore.{settings.aws_region}.amazonaws.com"
        f"/runtimes/{arn}/invocations?qualifier=DEFAULT"
    )


def agent_events(
    user: Annotated[User, Depends(get_user)],
    request: ChatRequest,
    session_id: Annotated[str, Depends(session_id_for)],
    settings: Annotated[Settings, Depends(get_settings)],
    http: Annotated[httpx2.Client, Depends(get_http)],
) -> Iterable[dict[str, Any]]:
    """Open the agent's stream before the response starts, so a refusal can
    still become a real 401, 503 or 502 instead of a broken stream."""
    req = http.build_request(
        "POST",
        agent_url(settings),
        headers={
            "Authorization": f"Bearer {user.token}",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
        },
        json={"message": request.message},
    )
    try:
        response = http.send(req, stream=True)
    except httpx2.HTTPError as err:
        logger.warning("agent unreachable error=%s", type(err).__name__)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The assistant failed.") from err
    if response.status_code != 200:
        response.close()
        logger.warning("agent refused status=%s", response.status_code)
        if response.status_code == 401:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Sign in to continue.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if response.status_code in (429, 503):
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "The assistant is busy. Try again in a few seconds.",
                headers={"Retry-After": "5"},
            )
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "The assistant failed.")
    return read_events(response)


def read_events(response: httpx2.Response) -> Iterator[dict[str, Any]]:
    """The agent's JSON events, one per SSE `data:` line, until the stream ends.

    Runtime frames what the agent yields as SSE. The agent yields JSON text, and
    Runtime JSON-encodes that text once more, hence the double decode.
    """
    try:
        for line in response.iter_lines():
            if not line.startswith("data:"):
                continue  # blank separators, keep-alive comments
            payload = json.loads(line[len("data:") :].strip())
            yield json.loads(payload) if isinstance(payload, str) else payload
    finally:
        response.close()


def to_sources(raw: str) -> list[dict[str, Any]]:
    """Citation cards from a Retrieve result. Any other tool's result gives [].

    Numbered in the order the agent saw them, which is what its [1], [2] markers mean.
    """
    try:
        results = json.loads(raw)["retrievalResults"]
        return [
            {
                "n": n,
                "title": r.get("metadata", {}).get("_document_title", "document"),
                "score": round(r.get("score", 0.0), 3),
                "excerpt": r["content"]["text"][:_EXCERPT_CHARS],
            }
            for n, r in enumerate(results, start=1)
        ]
    except (ValueError, KeyError, TypeError):
        return []


def relay(events: Iterable[dict[str, Any]]) -> Iterator[ServerSentEvent]:
    """Translate the agent's events into our small SSE vocabulary."""
    for event in events:
        kind = event.get("type")
        if kind == "text":
            if event.get("text"):
                # JSON-encoded on the wire, so a newline in the text cannot break SSE framing.
                yield ServerSentEvent(event="delta", data=event["text"])
        elif kind == "tool":
            yield ServerSentEvent(
                event="tool", data={"name": event["name"], "input": event["input"]}
            )
        elif kind == "tool_result":
            # ponytail: each search sends its own list, numbered from 1.
            # Two searches in one answer means two lists; the UI shows the latest.
            sources = to_sources(event.get("text", ""))
            if sources:
                yield ServerSentEvent(event="sources", data=sources)
        elif kind == "usage":
            yield ServerSentEvent(
                event="usage",
                data={
                    "input_tokens": event["input_tokens"],
                    "output_tokens": event["output_tokens"],
                    "model_calls": event["model_calls"],
                },
            )
        elif kind == "error":
            logger.warning("assistant failed mid-answer message=%s", event.get("message"))
            yield ServerSentEvent(
                event="error", data={"message": "The assistant stopped unexpectedly."}
            )
            return


@router.post("/v1/chat", response_class=EventSourceResponse)
def chat(
    user_id: Annotated[str, Depends(get_user_id)],
    session_id: Annotated[str, Depends(session_id_for)],
    events: Annotated[Iterable[dict[str, Any]], Depends(agent_events)],
) -> Iterator[ServerSentEvent]:
    # Plain `def`: the HTTP client blocks while waiting for the next line, so
    # FastAPI runs this generator in a worker thread and the server stays free.
    # https://fastapi.tiangolo.com/tutorial/server-sent-events/
    yield ServerSentEvent(event="session", data={"session_id": session_id})
    try:
        for sse in relay(events):
            yield sse
            if sse.event == "error":
                return
            if sse.event == "usage":
                # One line per answer: who, how many tokens. Never the text.
                logger.info("chat completed user=%s usage=%s", user_id, sse.data)
    except (httpx2.HTTPError, ValueError) as err:
        # The 200 is already sent, so the failure can only be reported inside the stream.
        logger.warning("assistant stream broke user=%s error=%s", user_id, type(err).__name__)
        yield ServerSentEvent(
            event="error", data={"message": "The assistant stopped unexpectedly."}
        )
        return
    yield ServerSentEvent(event="done", raw_data="[DONE]")
