"""Configuración de la aplicación, leída del entorno.

Una única clase `Settings` de pydantic-settings, cacheada con `get_settings()`. Aquí es
donde se añade cualquier variable de entorno nueva del backend.
"""

import os
from functools import lru_cache
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# El fichero .env es una comodidad de desarrollo local: Render y Docker inyectan
# variables de entorno reales y no llevan ningún .env. Que la ruta sea configurable es lo
# que permite a los tests salirse del todo -- tests/conftest.py pone ENV_FILE a cadena
# vacía, que significa "no leas ningún fichero", así que Settings cae a los valores por
# defecto de abajo y no a la base de datos que el desarrollador tenga configurada.
_ENV_FILE = os.getenv("ENV_FILE", ".env") or None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    environment: Literal["local", "preview", "production"] = "local"
    project_name: str = "Booking App API"
    # NoDecode es obligatorio: sin él pydantic-settings intenta decodificar el valor
    # bruto como JSON antes de que corra ningún validador, así que un CORS_ORIGINS
    # separado por comas lanza SettingsError al arrancar y split_cors_origins nunca
    # llega a ejecutarse.
    # Por defecto, ningún origen: un despliegue que se olvide de CORS_ORIGINS tiene que
    # fallar cerrado, no permitir en silencio el localhost de un desarrollador. En local
    # el origen sale de .env.example o de docker-compose.yml, donde está explícito.
    cors_origins: Annotated[list[str], NoDecode] = []
    database_url: str = "postgresql://postgres:postgres@localhost:5432/booking_app"
    # Sin valor significa "Sentry apagado": es lo normal en local y en CI, y solo los
    # entornos desplegados lo definen.
    sentry_dsn: str | None = None
    # La zona horaria del dueño: las reservas se guardan en UTC, pero las reglas de
    # disponibilidad se expresan en su reloj de pared local. Un dueño y un calendario,
    # así que esto es configuración y no una columna. Ver app/core/timezone.py.
    booking_timezone: str = "Europe/Madrid"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("booking_timezone")
    @classmethod
    def validate_booking_timezone(cls, value: str) -> str:
        # Fallar al arrancar y no en la primera reserva: una errata aquí se quedaría
        # dormida hasta que alguien intentase leer el calendario.
        #
        # Se relanza como ValueError a propósito. ZoneInfoNotFoundError hereda de
        # KeyError, que pydantic no convierte en ValidationError, así que sin envolverlo
        # sale un KeyError pelado que ni siquiera dice de qué campo se trata.
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Unknown timezone: {value!r}") from exc
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
