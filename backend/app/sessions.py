"""Past conversations for the chat sidebar, read from the harness's AgentCore Memory.

    GET /v1/sessions                          this tenant's conversations, newest first
    GET /v1/sessions/{session_id}/messages    one conversation, oldest message first

The harness writes Memory itself. One turn with one search becomes about ten events:
a "conversational" event per message (question, tool call, tool result, answer),
each holding the message as JSON text, plus "blob" events with the agent's
internal state. Only the questions and the answer text come back from here.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Literal

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel

from app.aws import get_agentcore, upstream_error
from app.chat import SESSION_ID_PATTERN
from app.settings import Settings, get_settings
from app.tenancy import get_tenant_id

if TYPE_CHECKING:
    from mypy_boto3_bedrock_agentcore import BedrockAgentCoreClient
    from mypy_boto3_bedrock_agentcore.type_defs import PayloadTypeOutputTypeDef

router = APIRouter(prefix="/v1/sessions")


class SessionSummary(BaseModel):
    session_id: str
    created_at: datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str


@router.get("")
def list_sessions(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated["BedrockAgentCoreClient", Depends(get_agentcore)],
) -> list[SessionSummary]:
    try:
        # ponytail: one page, the first 100 conversations. Paginate when the sidebar needs more.
        # https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore/client/list_sessions.html
        response = client.list_sessions(
            memoryId=settings.memory_id, actorId=tenant_id, maxResults=100
        )
        summaries = [
            SessionSummary(session_id=s["sessionId"], created_at=s["createdAt"])
            for s in response["sessionSummaries"]
            if has_events(client, settings.memory_id, tenant_id, s["sessionId"])
        ]
    except (ClientError, BotoCoreError) as err:
        raise upstream_error(err, "Listing conversations") from err
    return sorted(summaries, key=lambda s: s.created_at, reverse=True)


def has_events(
    client: "BedrockAgentCoreClient", memory_id: str, actor_id: str, session_id: str
) -> bool:
    """False for a conversation whose events were all deleted.

    AgentCore can delete events but not the conversation itself, so a wiped
    chat stays in the list. The sidebar hides those instead of showing them empty.
    ponytail: one extra call per conversation. Ceiling: slow with hundreds of chats.
    """
    page = client.list_events(
        memoryId=memory_id, sessionId=session_id, actorId=actor_id, maxResults=1
    )
    return bool(page["events"])


@router.get("/{session_id}/messages")
def list_messages(
    session_id: Annotated[str, Path(pattern=SESSION_ID_PATTERN)],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated["BedrockAgentCoreClient", Depends(get_agentcore)],
) -> list[ChatMessage]:
    # actorId=tenant_id: another tenant's session id finds nothing here.
    request: dict[str, Any] = {
        "memoryId": settings.memory_id,
        "sessionId": session_id,
        "actorId": tenant_id,
        "includePayloads": True,
        "maxResults": 100,
    }
    events = []
    try:
        # A long conversation spans several pages; nextToken asks for the next one.
        # https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agentcore/client/list_events.html
        while True:
            page = client.list_events(**request)
            events.extend(page["events"])
            if "nextToken" not in page:
                break
            request["nextToken"] = page["nextToken"]
    except (ClientError, BotoCoreError) as err:
        raise upstream_error(err, "Loading the conversation") from err

    events.sort(key=lambda e: e["eventTimestamp"])
    return [
        message
        for event in events
        for item in event.get("payload", [])
        if (message := to_chat_message(item)) is not None
    ]


def to_chat_message(item: "PayloadTypeOutputTypeDef") -> ChatMessage | None:
    """One Memory payload item as a sidebar message, or None if it is not a question or answer."""
    conversational = item.get("conversational")
    if conversational is None:
        return None  # a blob: the agent's internal state
    try:
        message = json.loads(conversational["content"]["text"])["message"]
        text = "".join(block.get("text", "") for block in message["content"])
        role = message["role"]
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    # Tool calls and tool results have no text blocks, so they drop out here.
    if role not in ("user", "assistant") or not text.strip():
        return None
    return ChatMessage(role=role, text=text)
