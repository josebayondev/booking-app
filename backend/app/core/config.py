from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["local", "production"] = "local"
    project_name: str = "Booking App API"


@lru_cache
def get_settings() -> Settings:
    return Settings()
