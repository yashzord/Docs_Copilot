"""Documents: upload a file, then let the Knowledge Base index it.

    POST /v1/documents               upload one file (multipart form, field "file"), start a sync
    GET  /v1/documents               list this tenant's files
    GET  /v1/documents/sync/{job_id} how that sync is going

Each upload writes two objects to S3:

    tenants/dev/handbook.pdf                  the file
    tenants/dev/handbook.pdf.metadata.json    {"metadataAttributes": {"tenant_id": "dev"}}

The second one is how the Knowledge Base learns which tenant every chunk of the
file belongs to, so a search can be filtered to one tenant (docs/learning/aws.md 7.4a).
https://docs.aws.amazon.com/bedrock/latest/userguide/s3-data-source-connector.html
"""

import json
import logging
import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status
from pydantic import BaseModel

from app.aws import get_kb_admin, get_s3, upstream_error
from app.settings import Settings, get_settings
from app.tenancy import get_tenant_id

if TYPE_CHECKING:
    from mypy_boto3_bedrock_agent import AgentsforBedrockClient
    from mypy_boto3_s3 import S3Client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/documents")

# File types the Knowledge Base parses. It skips anything else during a sync.
ALLOWED_SUFFIXES = frozenset({".pdf", ".md", ".txt", ".html", ".docx", ".csv"})
# The Knowledge Base skips files over 50 MB, so refuse them here instead.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
# Anything that is not a letter, digit, dot, dash or underscore becomes "_".
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
# A data source runs one ingestion job at a time. Starting a second one fails with
# one of these codes. The file is already uploaded, so the next sync picks it up.
_SYNC_BUSY_CODES = frozenset({"ConflictException", "ServiceQuotaExceededException"})


class Uploaded(BaseModel):
    key: str
    # None when another sync was already running.
    ingestion_job_id: str | None


class Document(BaseModel):
    name: str
    size: int
    last_modified: datetime


class SyncStatus(BaseModel):
    status: str
    scanned: int
    indexed: int
    failed: int
    failure_reasons: list[str]


def tenant_prefix(tenant_id: str) -> str:
    return f"tenants/{tenant_id}/"


def safe_filename(raw: str | None) -> str:
    """Keep only the file's own name, in safe characters.

    "../../etc/x.md" or "C:\\docs\\x.md" become "x.md", so a name can never
    point outside the tenant's folder.
    """
    name = re.split(r"[\\/]", raw or "")[-1]
    name = _UNSAFE_CHARS.sub("_", name).strip("._")[:200]
    if not name:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "File name is empty.")
    return name


def start_sync(kb: "AgentsforBedrockClient", settings: Settings) -> str | None:
    """Ask the Knowledge Base to scan the bucket again. Returns the job id, or None if busy."""
    try:
        # https://docs.aws.amazon.com/boto3/latest/reference/services/bedrock-agent/client/start_ingestion_job.html
        response = kb.start_ingestion_job(
            knowledgeBaseId=settings.kb_id, dataSourceId=settings.kb_data_source_id
        )
    except ClientError as err:
        if err.response.get("Error", {}).get("Code") in _SYNC_BUSY_CODES:
            # ponytail: the upload is kept but not indexed until the next sync starts.
            # Upgrade: a "sync now" button, or retry once the running job finishes.
            logger.info("sync already running, upload waits for the next one")
            return None
        raise upstream_error(err, "Starting the sync") from err
    except BotoCoreError as err:
        raise upstream_error(err, "Starting the sync") from err
    return response["ingestionJob"]["ingestionJobId"]


@router.post("", status_code=status.HTTP_201_CREATED)
def upload(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    file: UploadFile,
    settings: Annotated[Settings, Depends(get_settings)],
    s3: Annotated["S3Client", Depends(get_s3)],
    kb: Annotated["AgentsforBedrockClient", Depends(get_kb_admin)],
) -> Uploaded:
    # UploadFile keeps the body in a temporary file, not in memory.
    # https://fastapi.tiangolo.com/tutorial/request-files/
    name = safe_filename(file.filename)
    if PurePosixPath(name).suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Allowed file types: {', '.join(sorted(ALLOWED_SUFFIXES))}",
        )
    if file.size is None or file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Files must be 50 MB or smaller.")

    key = tenant_prefix(tenant_id) + name
    label = {"metadataAttributes": {"tenant_id": tenant_id}}
    try:
        # The label goes first. If the second write fails, what is left is a label
        # with no file (harmless), never a file with no tenant.
        s3.put_object(
            Bucket=settings.s3_bucket,
            Key=f"{key}.metadata.json",
            Body=json.dumps(label).encode(),
            ContentType="application/json",
        )
        # upload_fileobj streams the file in parts, so size does not matter.
        # https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/upload_fileobj.html
        s3.upload_fileobj(
            file.file,
            settings.s3_bucket,
            key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
    except (ClientError, BotoCoreError) as err:
        raise upstream_error(err, "Upload") from err

    logger.info("document uploaded tenant=%s bytes=%d", tenant_id, file.size)
    return Uploaded(key=key, ingestion_job_id=start_sync(kb, settings))


@router.get("")
def list_documents(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    settings: Annotated[Settings, Depends(get_settings)],
    s3: Annotated["S3Client", Depends(get_s3)],
) -> list[Document]:
    prefix = tenant_prefix(tenant_id)
    try:
        # ponytail: one page, so the first 1,000 objects. Paginate when a tenant has more.
        response = s3.list_objects_v2(Bucket=settings.s3_bucket, Prefix=prefix)
    except (ClientError, BotoCoreError) as err:
        raise upstream_error(err, "Listing documents") from err
    return [
        Document(
            name=obj["Key"].removeprefix(prefix),
            size=obj["Size"],
            last_modified=obj["LastModified"],
        )
        for obj in response.get("Contents", [])
        if not obj["Key"].endswith(".metadata.json")
    ]


@router.get("/sync/{job_id}")
def sync_status(
    # Ingestion job ids are 10 capital letters and digits, e.g. JL5NEA0617.
    job_id: Annotated[str, Path(pattern=r"^[A-Z0-9]{10}$")],
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    settings: Annotated[Settings, Depends(get_settings)],
    kb: Annotated["AgentsforBedrockClient", Depends(get_kb_admin)],
) -> SyncStatus:
    # A sync covers the whole bucket, not one tenant, so any tenant may ask about it.
    # It only reveals counts, never names or content.
    try:
        job = kb.get_ingestion_job(
            knowledgeBaseId=settings.kb_id,
            dataSourceId=settings.kb_data_source_id,
            ingestionJobId=job_id,
        )["ingestionJob"]
    except (ClientError, BotoCoreError) as err:
        raise upstream_error(err, "Checking the sync") from err
    stats = job.get("statistics", {})
    return SyncStatus(
        status=job["status"],
        scanned=stats.get("numberOfDocumentsScanned", 0),
        indexed=stats.get("numberOfNewDocumentsIndexed", 0)
        + stats.get("numberOfModifiedDocumentsIndexed", 0),
        failed=stats.get("numberOfDocumentsFailed", 0),
        failure_reasons=job.get("failureReasons", []),
    )
