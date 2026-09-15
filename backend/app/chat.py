"""POST /v1/chat: one question in, the agent's answer out as Server-Sent Events.

The agent is the AgentCore Harness (lesson 17). It keeps the
conversation in AgentCore Memory, so the browser sends only the new message
and a session id, never the history.

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
from typing import TYPE_CHECKING, Annotated, Any

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field

from app.aws import get_agentcore, upstream_error
from app.settings import Settings, get_settings
from app.tenancy import get_tenant_id

if TYPE_CHECKING:
    from mypy_boto3_bedrock_agentcore import BedrockAgentCoreClient
    from mypy_boto3_bedrock_agentcore.type_defs import InvokeHarnessStreamOutputTypeDef

logger = logging.getLogger(__name__)
router = APIRouter()

# InvokeHarness accepts 33 to 100 letters, digits, dashes or underscores, starting
# with a letter or digit (read from the API model in boto3, 2026-09-11).
SESSION_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_-]{32,99}$"
# Stream events that mean the agent failed after it started answering.
_ERROR_EVENTS = ("internalServerException", "validationException", "runtimeClientError")
_EXCERPT_CHARS = 300


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    # Leave out to start a new conversation; the first event carries the new id.
    session_id: str | None = Field(default=None, pattern=SESSION_ID_PATTERN)


def session_id_for(request: ChatRequest) -> str:
    # A UUID is 36 characters, inside the 33 to 100 the harness accepts.
    # FastAPI runs this once per request, so every dependency sees the same id.
    return request.session_id or str(uuid.uuid4())


def harness_stream(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    request: ChatRequest,
    session_id: Annotated[str, Depends(session_id_for)],
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated["BedrockAgentCoreClient", Depends(get_agentcore)],
) -> Iterable["InvokeHarnessStreamOutputTypeDef"]:
    """Open the agent's stream before the response starts, so a refusal can
    still become a real 503 or 502 (lesson 6)."""
    try:
        # https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore/client/invoke_harness.html
        response = client.invoke_harness(
            harnessArn=settings.harness_arn,
            runtimeSessionId=session_id,
            # Memory is stored per actor and session, so one tenant can never load
            # another tenant's conversation by guessing a session id.
            # ponytail: one actor per tenant. With a login, it would be the signed-in user.
            actorId=tenant_id,
            messages=[{"role": "user", "content": [{"text": request.message}]}],
        )
    except (ClientError, BotoCoreError) as err:
        raise upstream_error(err, "The assistant") from err
    return response["stream"]


def parse_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except ValueError:
        return raw


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


def relay(events: Iterable["InvokeHarnessStreamOutputTypeDef"]) -> Iterator[ServerSentEvent]:
    """Translate the harness's raw events into our small SSE vocabulary.

    The harness streams every step of its loop (lesson 16): the
    model's reasoning, a tool call, the tool's result, then the answer. Each
    content block arrives as start, several deltas, stop, so a tool call's input
    and a tool's result are collected until their block stops.
    """
    tool: dict[str, str] | None = None  # the tool call being streamed
    result: list[str] | None = None  # pieces of the tool result being streamed
    usage = {"input_tokens": 0, "output_tokens": 0, "model_calls": 0}

    for event in events:
        if "contentBlockStart" in event:
            start = event["contentBlockStart"]["start"]
            if "toolUse" in start:
                tool = {"name": start["toolUse"]["name"], "input": ""}
            elif "toolResult" in start:
                result = []
        elif "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            if "text" in delta:
                # JSON-encoded on the wire, so a newline in the text cannot break SSE framing.
                yield ServerSentEvent(event="delta", data=delta["text"])
            elif "toolUse" in delta and tool is not None:
                tool["input"] += delta["toolUse"]["input"]
            elif "toolResult" in delta and result is not None:
                result.extend(part.get("text", "") for part in delta["toolResult"])
            # reasoningContent is the model thinking out loud. Not shown to the user.
        elif "contentBlockStop" in event:
            if tool is not None:
                yield ServerSentEvent(
                    event="tool", data={"name": tool["name"], "input": parse_json(tool["input"])}
                )
                tool = None
            if result is not None:
                # ponytail: each search sends its own list, numbered from 1.
                # Two searches in one answer means two lists; the UI shows the latest.
                sources = to_sources("".join(result))
                if sources:
                    yield ServerSentEvent(event="sources", data=sources)
                result = None
        elif "metadata" in event:
            # One metadata event per model call; an answer with one search takes two calls.
            counts = event["metadata"]["usage"]
            usage["input_tokens"] += counts["inputTokens"]
            usage["output_tokens"] += counts["outputTokens"]
            usage["model_calls"] += 1
        else:
            failure = next((name for name in _ERROR_EVENTS if name in event), None)
            if failure is not None:
                logger.warning("assistant failed mid-answer event=%s", failure)
                yield ServerSentEvent(
                    event="error", data={"message": "The assistant stopped unexpectedly."}
                )
                return

    yield ServerSentEvent(event="usage", data=usage)


@router.post("/v1/chat", response_class=EventSourceResponse)
def chat(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    session_id: Annotated[str, Depends(session_id_for)],
    events: Annotated[Iterable["InvokeHarnessStreamOutputTypeDef"], Depends(harness_stream)],
) -> Iterator[ServerSentEvent]:
    # Plain `def`: boto3 blocks while waiting for the next event, so FastAPI runs
    # this generator in a worker thread and the server stays free.
    # https://fastapi.tiangolo.com/tutorial/server-sent-events/
    yield ServerSentEvent(event="session", data={"session_id": session_id})
    try:
        for sse in relay(events):
            yield sse
            if sse.event == "error":
                return
            if sse.event == "usage":
                # One line per answer: who, how many tokens. Never the text.
                logger.info("chat completed tenant=%s usage=%s", tenant_id, sse.data)
    except (ClientError, BotoCoreError) as err:
        # The 200 is already sent, so the failure can only be reported inside the stream.
        logger.warning("assistant stream broke tenant=%s error=%s", tenant_id, type(err).__name__)
        yield ServerSentEvent(
            event="error", data={"message": "The assistant stopped unexpectedly."}
        )
        return
    yield ServerSentEvent(event="done", raw_data="[DONE]")
