"""AWS clients, one per service, shared by every request. Plus one way to report AWS failures.

boto3 clients are safe to share across threads, so each is built once (lru_cache).
Tests replace them through FastAPI's dependency overrides.
"""

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from app.settings import get_settings

if TYPE_CHECKING:
    # Type-only imports from boto3-stubs (dev dependency), never loaded at runtime.
    from mypy_boto3_bedrock_agent import AgentsforBedrockClient
    from mypy_boto3_bedrock_agentcore import BedrockAgentCoreClient
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)

# "standard" retries throttling and network blips, 3 attempts in total.
# boto3 still defaults to "legacy", so this is set on purpose.
# https://docs.aws.amazon.com/boto3/latest/guide/retries.html
_RETRIES = Config(retries={"mode": "standard"})

# Error codes that mean "busy, try again soon". Everything else is a 502.
_RETRYABLE_CODES = frozenset(
    {"ThrottlingException", "ServiceUnavailableException", "TooManyRequestsException"}
)


def _session() -> boto3.Session:
    settings = get_settings()
    return boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)


@lru_cache
def get_s3() -> "S3Client":
    return _session().client("s3", config=_RETRIES)


@lru_cache
def get_kb_admin() -> "AgentsforBedrockClient":
    # "bedrock-agent" is the Knowledge Base control API: start and check ingestion jobs.
    return _session().client("bedrock-agent", config=_RETRIES)


@lru_cache
def get_agentcore() -> "BedrockAgentCoreClient":
    # The AgentCore data API signed with our own AWS credentials: Memory reads
    # for the sidebar. The Harness is not called this way any more (see below).
    return _session().client("bedrock-agentcore", config=_RETRIES)


@lru_cache(maxsize=64)
def harness_client(token: str) -> "BedrockAgentCoreClient":
    """A bedrock-agentcore client that speaks for one signed-in user.

    The Harness has an inbound JWT authorizer (lesson 22), so it wants the user's
    Cognito token in `Authorization: Bearer ...`, not an AWS signature. boto3 has no
    switch for that, so: signing is turned off (UNSIGNED), and a hook adds the
    header to every InvokeHarness call just before it is sent. The client still
    parses the event stream for us, which is the part worth keeping.
    Cached per token: a token lives an hour and the same user asks many times.
    An agent can go quiet while it searches or thinks, so wait up to 5 minutes
    for the next byte instead of boto3's default 60 seconds.
    https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-security.html#_inbound_oauth
    https://boto3.amazonaws.com/v1/documentation/api/latest/guide/events.html
    """
    client = _session().client(
        "bedrock-agentcore",
        config=_RETRIES.merge(Config(signature_version=UNSIGNED, read_timeout=300)),
    )

    def add_bearer(params: dict[str, Any], **_: Any) -> None:
        params["headers"]["Authorization"] = f"Bearer {token}"

    client.meta.events.register("before-call.bedrock-agentcore.InvokeHarness", add_bearer)
    return client


def upstream_error(err: ClientError | BotoCoreError, action: str) -> HTTPException:
    """Log an AWS failure and turn it into a 503 (busy) or 502 (failed).

    Logs the error code and request id: enough to find the call in AWS, and no
    user content. AWS's own message never goes back to the caller.
    https://docs.aws.amazon.com/boto3/latest/guide/error-handling.html
    """
    if isinstance(err, ClientError):
        # ClientError = AWS answered, and the answer was an error.
        code = err.response.get("Error", {}).get("Code", "Unknown")
        request_id = err.response.get("ResponseMetadata", {}).get("RequestId", "-")
        logger.warning("%s failed code=%s request_id=%s", action, code, request_id)
        if code in _RETRYABLE_CODES:
            return HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AWS is busy. Try again in a few seconds.",
                headers={"Retry-After": "5"},
            )
    else:
        # BotoCoreError = never got a proper answer (network, timeout, local config).
        logger.warning("%s failed error=%s", action, type(err).__name__)
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{action} failed.")
