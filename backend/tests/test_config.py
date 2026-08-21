"""Tests de app/core/config.py: parseo de CORS_ORIGINS, validación de la zona horaria y
que el .env.example commiteado sigue cargando."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parent.parent


class IsolatedSettings(Settings):
    """Ignora cualquier .env local para que estos tests solo vean lo que ellos fijan."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


class EnvExampleSettings(Settings):
    """Carga el .env.example commiteado, que es el que el README manda copiar."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env.example", extra="ignore")


# conftest.py fija CORS_ORIGINS, SENTRY_DSN y compañía para toda la suite, y si no tendrían
# prioridad tanto sobre env_file=None como sobre .env.example, haciendo que estos tests
# pasasen por el motivo equivocado.
pytestmark = pytest.mark.usefixtures("clean_env")


def test_cors_origins_defaults_to_empty() -> None:
    """Fallar cerrado: olvidarse de CORS_ORIGINS tiene que no permitir nada, no localhost."""
    assert IsolatedSettings().cors_origins == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://a.example", ["https://a.example"]),
        (
            "https://a.example,https://b.example",
            ["https://a.example", "https://b.example"],
        ),
        (
            "  https://a.example , https://b.example  ",
            ["https://a.example", "https://b.example"],
        ),
        ("https://a.example,,", ["https://a.example"]),
    ],
)
def test_cors_origins_parses_comma_separated_env_var(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", raw)

    assert IsolatedSettings().cors_origins == expected


def test_env_example_loads() -> None:
    settings = EnvExampleSettings()

    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.environment == "local"
    assert settings.booking_timezone == "Europe/Madrid"


def test_booking_timezone_defaults_to_madrid() -> None:
    assert IsolatedSettings().booking_timezone == "Europe/Madrid"


def test_invalid_booking_timezone_fails_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Una errata aquí se quedaría dormida hasta que se leyese la primera reserva."""
    monkeypatch.setenv("BOOKING_TIMEZONE", "Mars/Olympus")

    with pytest.raises(ValidationError):
        IsolatedSettings()
