"""Talking to Amazon Bedrock.

Two jobs: open a streaming answer from a model, and turn Bedrock's raw
stream events into plain text pieces plus one usage record at the end.

Uses the Converse API, which has one request shape for every model on
Bedrock, so switching models is a config change, not a code change.
https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

import boto3
from botocore.config import Config

from app.settings import get_settings

if TYPE_CHECKING:
    # Type-only imports from boto3-stubs. They describe boto3's dict shapes to mypy
    # and are never imported at runtime, so they are dev-only dependencies.
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
    from mypy_boto3_bedrock_runtime.type_defs import (
        ConverseStreamOutputTypeDef,
        MessageTypeDef,
    )

Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class Usage:
    """Token counts and timing for one answer. Bedrock sends it as the last event."""

    input_tokens: int
    output_tokens: int
    latency_ms: int


@lru_cache
def get_bedrock_client() -> "BedrockRuntimeClient":
    """One client for the whole process. boto3 clients are safe to share across threads."""
    settings = get_settings()
    session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
    # "standard" retries throttling and transient network errors, 3 attempts in total.
    # boto3 still defaults to "legacy", so this is set on purpose.
    # Retries only cover opening the stream, never a stream that already started.
    # https://docs.aws.amazon.com/boto3/latest/guide/retries.html
    return session.client("bedrock-runtime", config=Config(retries={"mode": "standard"}))


def open_stream(
    client: "BedrockRuntimeClient",
    *,
    model_id: str,
    turns: Iterable[tuple[Role, str]],
    max_tokens: int,
) -> Iterable["ConverseStreamOutputTypeDef"]:
    """Start a streaming answer. Raises botocore errors if Bedrock refuses the call."""
    messages: list[MessageTypeDef] = [
        {"role": role, "content": [{"text": text}]} for role, text in turns
    ]
    # https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-runtime/client/converse_stream.html
    response = client.converse_stream(
        modelId=model_id,
        messages=messages,
        inferenceConfig={"maxTokens": max_tokens},
    )
    return response["stream"]


def text_and_usage(events: Iterable["ConverseStreamOutputTypeDef"]) -> Iterator[str | Usage]:
    """Yield each text piece as it arrives, then one Usage. Other event kinds are skipped.

    Event names come from the ConverseStream response syntax (link above open_stream).
    """
    for event in events:
        if "contentBlockDelta" in event:
            text = event["contentBlockDelta"]["delta"].get("text")
            if text:
                yield text
        elif "metadata" in event:
            metadata = event["metadata"]
            yield Usage(
                input_tokens=metadata["usage"]["inputTokens"],
                output_tokens=metadata["usage"]["outputTokens"],
                latency_ms=metadata["metrics"]["latencyMs"],
            )
