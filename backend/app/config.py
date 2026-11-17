"""Typed settings from environment variables. The app refuses to start without the required ones."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

API_PREFIX = "/api/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Async SQLAlchemy URL for the limited-privilege application role.
    database_url: SecretStr
    # Shared secret the web container sends, so the API can trust its x-client-key header.
    internal_token: SecretStr = Field(min_length=16)
    web_origin: str = "http://localhost:3000"
    enable_docs: bool = True
    log_level: str = "INFO"

    rate_limit_enabled: bool = True
    rate_limit_reads_per_minute: int = 120
    rate_limit_writes_per_minute: int = 20
    max_body_bytes: int = 64 * 1024
    db_timeout_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
