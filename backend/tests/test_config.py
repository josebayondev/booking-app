from pathlib import Path

import pytest
from pydantic_settings import SettingsConfigDict

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parent.parent


class IsolatedSettings(Settings):
    """Ignores any local .env so these tests only see what they set themselves."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


class EnvExampleSettings(Settings):
    """Loads the committed .env.example, which the README tells you to copy."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env.example", extra="ignore")


@pytest.fixture(autouse=True)
def _clear_cors_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)


def test_cors_origins_defaults_to_local_frontend() -> None:
    assert IsolatedSettings().cors_origins == ["http://localhost:5173"]


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
