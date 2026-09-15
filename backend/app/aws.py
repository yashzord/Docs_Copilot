"""AWS clients, one per service, shared by every request. Plus one way to report AWS failures.

boto3 clients are safe to share across threads, so each is built once (lru_cache).
Tests replace them through FastAPI's dependency overrides.
"""

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

import boto3
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
    # The AgentCore data API signed with our own AWS credentials: Memory reads for
    # the sidebar. The agent itself is called with the user's token (app/chat.py).
    return _session().client("bedrock-agentcore", config=_RETRIES)


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
