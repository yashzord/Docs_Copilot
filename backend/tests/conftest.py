"""Setup every test gets automatically: settings that never read backend/.env.

pytest loads conftest.py before any test file and applies its autouse fixtures.
https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files
"""

from collections.abc import Iterator

import pytest

from app.auth import User, get_user
from app.main import app
from app.settings import Settings, get_settings

TEST_SETTINGS = Settings(
    # _env_file=None: ignore backend/.env, so tests behave the same on every machine.
    _env_file=None,
    aws_profile=None,
    s3_bucket="test-bucket",
    kb_id="KB00000000",
    kb_data_source_id="DS00000000",
    graph_kb_id="GKB0000000",
    graph_data_source_id="GDS0000000",
    harness_arn="arn:aws:bedrock-agentcore:us-west-2:000000000000:harness/test",
    memory_id="test-memory",
    cognito_user_pool_id="us-west-2_TESTPOOL",
    cognito_client_id="testclientid",
)
# Every test runs as this signed-in user unless it overrides get_user itself.
# The token is never verified here: verification has its own tests (test_auth.py).
TEST_USER = User(id="user-a", token="test-token")  # noqa: S106 (not a secret)


@pytest.fixture(autouse=True)
def _test_settings() -> Iterator[None]:
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    app.dependency_overrides[get_user] = lambda: TEST_USER
    yield
    app.dependency_overrides.clear()
