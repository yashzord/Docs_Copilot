"""POST /v1/chat: send a conversation, get the answer back as Server-Sent Events.

Wire format, one event per piece:

    event: delta   data: "Hel"
    event: delta   data: "lo"
    event: usage   data: {"input_tokens": 5, "output_tokens": 2, "latency_ms": 120}
    event: done    data: [DONE]

or, if the model fails after streaming began:

    event: error   data: {"message": "..."}
"""

import dataclasses
import logging
from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Annotated, Self

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, Field, model_validator

from app.llm import Role, Usage, get_bedrock_client, open_stream, text_and_usage
from app.settings import Settings, get_settings
from app.tenancy import get_tenant_id

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
    from mypy_boto3_bedrock_runtime.type_defs import ConverseStreamOutputTypeDef

logger = logging.getLogger(__name__)
router = APIRouter()

# Bedrock error codes that mean "busy, try again soon". Everything else is a 502.
# Codes from the ConverseStream Exceptions list:
# https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse_stream.html
_RETRYABLE_CODES = frozenset(
    {"ThrottlingException", "ServiceUnavailableException", "ModelNotReadyException"}
)


# ---------- request shape: validated at the edge, before any money is spent ----------


class Message(BaseModel):
    role: Role
    # Limits keep one request from sending a novel to the model (cost) or
    # an empty turn (Bedrock rejects it anyway).
    content: str = Field(min_length=1, max_length=20_000)


class ChatRequest(BaseModel):
    # https://fastapi.tiangolo.com/tutorial/body/
    messages: list[Message] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def starts_and_ends_with_user(self) -> Self:
        # Bedrock rejects any other order with a ValidationException (checked live
        # 2026-09-10). Checking here returns a clear 422 without paying for a call.
        # https://pydantic.dev/docs/validation/latest/concepts/validators/#model-validators
        if self.messages[0].role != "user" or self.messages[-1].role != "user":
            raise ValueError("conversation must start and end with a user message")
        return self


# ---------- opening the model stream: done in a dependency, before the response starts ----------


def bedrock_stream(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    client: Annotated["BedrockRuntimeClient", Depends(get_bedrock_client)],
) -> Iterable["ConverseStreamOutputTypeDef"]:
    """Open the stream here so a refusal can still become a real HTTP status.

    Once the first event is sent, the status line (200) is already on the wire and
    cannot change. Dependencies run before that, so errors here become 503 or 502.
    """
    try:
        return open_stream(
            client,
            model_id=settings.bedrock_synth_model_id,
            turns=((m.role, m.content) for m in request.messages),
            max_tokens=settings.max_output_tokens,
        )
    except ClientError as err:
        # ClientError = AWS answered with an error. Log the code and request id
        # (actionable, no user content). Never forward AWS's message to the caller.
        # https://docs.aws.amazon.com/boto3/latest/guide/error-handling.html
        code = err.response.get("Error", {}).get("Code", "Unknown")
        request_id = err.response.get("ResponseMetadata", {}).get("RequestId", "-")
        logger.warning("bedrock refused call code=%s request_id=%s", code, request_id)
        if code in _RETRYABLE_CODES:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The model is busy. Try again in a few seconds.",
                headers={"Retry-After": "5"},
            ) from err
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="The model call failed."
        ) from err
    except BotoCoreError as err:
        # BotoCoreError = never reached AWS (network, timeout, bad local config).
        logger.warning("bedrock unreachable error=%s", type(err).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="The model call failed."
        ) from err


# ---------- the endpoint ----------


@router.post("/v1/chat", response_class=EventSourceResponse)
def chat(
    # Order matters: dependencies run top to bottom, so a bad tenant header
    # is rejected before Bedrock is ever called.
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    events: Annotated[Iterable["ConverseStreamOutputTypeDef"], Depends(bedrock_stream)],
) -> Iterator[ServerSentEvent]:
    # Plain `def`, not `async def`: boto3 blocks while waiting for the next event,
    # so FastAPI runs this generator in a worker thread and the server stays free.
    # https://fastapi.tiangolo.com/tutorial/server-sent-events/
    try:
        for item in text_and_usage(events):
            if isinstance(item, Usage):
                # One line per answer: who, how many tokens, how long. Never the text.
                logger.info(
                    "chat completed tenant=%s input_tokens=%d output_tokens=%d latency_ms=%d",
                    tenant_id,
                    item.input_tokens,
                    item.output_tokens,
                    item.latency_ms,
                )
                yield ServerSentEvent(event="usage", data=dataclasses.asdict(item))
            else:
                # `data` is JSON-encoded, so "Hel" goes out as "\"Hel\"". That keeps a
                # newline inside a token from breaking the SSE framing.
                yield ServerSentEvent(event="delta", data=item)
    except (ClientError, BotoCoreError) as err:
        # The 200 is already sent, so the failure can only be reported inside the stream.
        logger.warning("bedrock stream broke tenant=%s error=%s", tenant_id, type(err).__name__)
        yield ServerSentEvent(event="error", data={"message": "The model stopped unexpectedly."})
        return
    yield ServerSentEvent(event="done", raw_data="[DONE]")
