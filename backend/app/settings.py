"""Runtime configuration.

Read from real environment variables first, then from backend/.env.
Environment variables always win over the file, so Docker and ECS can set
values without any file at all.
https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ".env" is looked up in the folder the server starts from: backend/.
    # Unknown keys in the file are an error, so a typo fails loudly at startup.
    model_config = SettingsConfigDict(env_file=".env")

    # Field names map to env vars case-insensitively: aws_region <- AWS_REGION.

    # Named profile in ~/.aws. None means "use the default credential chain",
    # which is what containers on AWS do (they get credentials from their role).
    aws_profile: str | None = None
    aws_region: str = "us-west-2"

    # Everything below is required, no default: the app refuses to start without it.
    # IDs come from the AWS console; docs/learning/aws.md says where each one lives.

    # Documents: the bucket uploads go to, and the Knowledge Base that indexes it.
    s3_bucket: str
    kb_id: str
    kb_data_source_id: str
    # The GraphRAG Knowledge Base over the same bucket (D4). Uploads sync it too.
    graph_kb_id: str
    graph_data_source_id: str

    # The agent (our Strands agent on AgentCore Runtime, agent/src/main.py) and the
    # memory that keeps its conversations.
    agent_runtime_arn: str
    memory_id: str

    # Login: the Cognito user pool that signs users in, and the app client the
    # page uses. Both are public identifiers, not secrets (lesson 31).
    cognito_user_pool_id: str
    cognito_client_id: str

    @property
    def cognito_issuer(self) -> str:
        # The `iss` claim every token from this pool carries.
        # https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html
        return f"https://cognito-idp.{self.aws_region}.amazonaws.com/{self.cognito_user_pool_id}"

    @property
    def cognito_jwks_url(self) -> str:
        # Where the pool publishes the public keys that verify its signatures.
        return f"{self.cognito_issuer}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    # Built once, reused on every request. Tests swap it via dependency_overrides.
    # https://fastapi.tiangolo.com/advanced/settings/#creating-the-settings-only-once-with-lru_cache
    return Settings()
