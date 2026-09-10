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

    # Required, no default: the app refuses to start without a model.
    bedrock_synth_model_id: str

    # Caps the answer length, which caps the cost of one request.
    max_output_tokens: int = 1024


@lru_cache
def get_settings() -> Settings:
    # Built once, reused on every request. Tests swap it via dependency_overrides.
    # https://fastapi.tiangolo.com/advanced/settings/#creating-the-settings-only-once-with-lru_cache
    return Settings()
