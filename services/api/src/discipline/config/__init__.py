from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["dev", "staging", "prod"] = Field(default="dev", alias="DISCIPLINE_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")
    timescale_url: str = Field(alias="TIMESCALE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_endpoint_url: str | None = Field(default=None, alias="AWS_ENDPOINT_URL")
    s3_voice_bucket: str = Field(alias="S3_VOICE_BUCKET")
    s3_export_bucket: str = Field(alias="S3_EXPORT_BUCKET")
    kms_key_id: str = Field(alias="KMS_KEY_ID")

    clerk_secret_key: str = Field(alias="CLERK_SECRET_KEY")
    clerk_jwt_issuer: str = Field(alias="CLERK_JWT_ISSUER")
    server_session_secret: str = Field(alias="SERVER_SESSION_SECRET")

    anthropic_api_key: str = Field(alias="ANTHROPIC_API_KEY")
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com", alias="ANTHROPIC_BASE_URL"
    )

    stripe_secret_key: str = Field(alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(alias="STRIPE_WEBHOOK_SECRET")

    otel_endpoint: str = Field(
        default="http://localhost:4318", alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_service_name: str = Field(default="discipline-api", alias="OTEL_SERVICE_NAME")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
