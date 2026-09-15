"""Tests for /v1/documents.

S3 is moto's in-memory fake (real boto3 calls, no network). The Knowledge Base
is FakeKb: moto does not model ingestion jobs.
https://docs.getmoto.org/en/latest/docs/getting_started.html
"""

import json
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import boto3
import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from moto import mock_aws

from app import documents
from app.auth import get_user
from app.aws import get_kb_admin, get_s3
from app.main import app
from tests.conftest import TEST_SETTINGS
from tests.helpers import aws_error

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

BUCKET = TEST_SETTINGS.s3_bucket


JOB_IDS = {TEST_SETTINGS.kb_id: "JOB0000001", TEST_SETTINGS.graph_kb_id: "GRAPH00001"}


class FakeKb:
    """Stands in for the bedrock-agent client: records calls, returns canned answers.

    `error` fails every sync start; `graph_error` fails only the graph Knowledge Base's.
    """

    def __init__(
        self, error: ClientError | None = None, graph_error: ClientError | None = None
    ) -> None:
        self.error = error
        self.graph_error = graph_error
        self.calls: list[dict[str, Any]] = []

    def start_ingestion_job(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        if self.graph_error is not None and kwargs["knowledgeBaseId"] == TEST_SETTINGS.graph_kb_id:
            raise self.graph_error
        job_id = JOB_IDS[kwargs["knowledgeBaseId"]]
        return {"ingestionJob": {"ingestionJobId": job_id, "status": "STARTING"}}

    def get_ingestion_job(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "ingestionJob": {
                "status": "COMPLETE",
                "statistics": {
                    "numberOfDocumentsScanned": 3,
                    "numberOfNewDocumentsIndexed": 1,
                    "numberOfModifiedDocumentsIndexed": 1,
                    "numberOfDocumentsFailed": 0,
                },
            }
        }


@pytest.fixture
def s3(monkeypatch: pytest.MonkeyPatch) -> Iterator["S3Client"]:
    # Fake credentials, so nothing here can ever reach a real account.
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    with mock_aws():
        client = boto3.client("s3", region_name="us-west-2")
        client.create_bucket(
            Bucket=BUCKET, CreateBucketConfiguration={"LocationConstraint": "us-west-2"}
        )
        yield client


def client_using(s3: "S3Client", kb: FakeKb) -> TestClient:
    app.dependency_overrides[get_s3] = lambda: s3
    app.dependency_overrides[get_kb_admin] = lambda: kb
    return TestClient(app)


def upload(client: TestClient, name: str, body: bytes = b"# Handbook") -> Any:
    return client.post("/v1/documents", files={"file": (name, body, "text/markdown")})


def read_json(s3: "S3Client", key: str) -> Any:
    return json.loads(s3.get_object(Bucket=BUCKET, Key=key)["Body"].read())


# ---------- upload: happy path ----------


def test_upload_writes_file_and_user_label_then_starts_both_syncs(s3: "S3Client") -> None:
    kb = FakeKb()

    response = upload(client_using(s3, kb), "hand book.md")

    assert response.status_code == 201
    assert response.json() == {
        "key": "users/user-a/hand_book.md",
        "ingestion_job_id": "JOB0000001",
        "graph_ingestion_job_id": "GRAPH00001",
    }
    stored = s3.get_object(Bucket=BUCKET, Key="users/user-a/hand_book.md")["Body"].read()
    assert stored == b"# Handbook"
    assert read_json(s3, "users/user-a/hand_book.md.metadata.json") == {
        "metadataAttributes": {"user-a": "owner"}
    }
    assert kb.calls == [
        {"knowledgeBaseId": "KB00000000", "dataSourceId": "DS00000000"},
        {"knowledgeBaseId": "GKB0000000", "dataSourceId": "GDS0000000"},
    ]


def test_upload_while_a_sync_runs_keeps_the_file_without_a_job(s3: "S3Client") -> None:
    kb = FakeKb(error=aws_error("ConflictException"))

    response = upload(client_using(s3, kb), "a.md")

    assert response.status_code == 201
    assert response.json()["ingestion_job_id"] is None
    assert response.json()["graph_ingestion_job_id"] is None
    assert s3.head_object(Bucket=BUCKET, Key="users/user-a/a.md")


def test_graph_sync_busy_leaves_the_main_sync_running(s3: "S3Client") -> None:
    kb = FakeKb(graph_error=aws_error("ConflictException"))

    response = upload(client_using(s3, kb), "a.md")

    assert response.status_code == 201
    assert response.json()["ingestion_job_id"] == "JOB0000001"
    assert response.json()["graph_ingestion_job_id"] is None


def test_graph_sync_refused_does_not_fail_the_upload(s3: "S3Client") -> None:
    kb = FakeKb(graph_error=aws_error("AccessDeniedException"))

    response = upload(client_using(s3, kb), "a.md")

    assert response.status_code == 201
    assert response.json()["ingestion_job_id"] == "JOB0000001"
    assert response.json()["graph_ingestion_job_id"] is None
    assert s3.head_object(Bucket=BUCKET, Key="users/user-a/a.md")


@pytest.mark.parametrize(
    ("raw", "stored"),
    [
        ("../../etc/passwd.md", "passwd.md"),
        ("C:\\docs\\x.md", "x.md"),
        ("..hidden.md", "hidden.md"),
    ],
)
def test_file_name_can_never_leave_the_users_folder(s3: "S3Client", raw: str, stored: str) -> None:
    response = upload(client_using(s3, FakeKb()), raw)

    assert response.json()["key"] == f"users/user-a/{stored}"


# ---------- upload: refused before anything is written ----------


def test_unsupported_type_is_415_and_writes_nothing(s3: "S3Client") -> None:
    kb = FakeKb()

    response = upload(client_using(s3, kb), "tool.exe")

    assert response.status_code == 415
    assert "Contents" not in s3.list_objects_v2(Bucket=BUCKET)
    assert kb.calls == []


def test_too_large_is_413(s3: "S3Client", monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(documents, "MAX_UPLOAD_BYTES", 3)

    response = upload(client_using(s3, FakeKb()), "a.md", body=b"1234")

    assert response.status_code == 413


def test_not_signed_in_is_401_and_writes_nothing(s3: "S3Client") -> None:
    client = client_using(s3, FakeKb())
    del app.dependency_overrides[get_user]  # the real check, not the test user

    response = upload(client, "a.md")

    assert response.status_code == 401
    assert "Contents" not in s3.list_objects_v2(Bucket=BUCKET)


def test_sync_refused_for_another_reason_is_502(s3: "S3Client") -> None:
    response = upload(client_using(s3, FakeKb(error=aws_error("AccessDeniedException"))), "a.md")

    assert response.status_code == 502
    assert "AccessDenied" not in response.text


# ---------- list ----------


def test_list_shows_only_this_users_files_without_labels(s3: "S3Client") -> None:
    for key in ("users/user-a/a.md", "users/user-a/a.md.metadata.json", "users/user-b/b.md"):
        s3.put_object(Bucket=BUCKET, Key=key, Body=b"x")

    response = client_using(s3, FakeKb()).get("/v1/documents")

    assert response.status_code == 200
    assert [d["name"] for d in response.json()] == ["a.md"]


# ---------- sync status ----------


def test_sync_status_adds_new_and_modified_as_indexed(s3: "S3Client") -> None:
    response = client_using(s3, FakeKb()).get("/v1/documents/sync/JOB0000001")

    assert response.status_code == 200
    assert response.json() == {
        "status": "COMPLETE",
        "scanned": 3,
        "indexed": 2,
        "failed": 0,
        "failure_reasons": [],
    }


def test_sync_status_rejects_a_malformed_job_id(s3: "S3Client") -> None:
    kb = FakeKb()

    response = client_using(s3, kb).get("/v1/documents/sync/not-a-job")

    assert response.status_code == 422
    assert kb.calls == []
