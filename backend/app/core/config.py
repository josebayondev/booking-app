from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["local", "preview", "production"] = "local"
    project_name: str = "Booking App API"
    # NoDecode is required: without it pydantic-settings tries to JSON-decode the
    # raw value before any validator runs, so a comma-separated CORS_ORIGINS
    # raises SettingsError at startup and split_cors_origins never gets called.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    database_url: str = "postgresql://postgres:postgres@localhost:5432/booking_app"
    # Unset means "Sentry off": that is the default locally and in CI, and only
    # the deployed environments define it.
    sentry_dsn: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
