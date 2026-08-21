from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parent.parent


class IsolatedSettings(Settings):
    """Ignores any local .env so these tests only see what they set themselves."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


class EnvExampleSettings(Settings):
    """Loads the committed .env.example, which the README tells you to copy."""

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env.example", extra="ignore")


# conftest.py pins CORS_ORIGINS, SENTRY_DSN and friends for the whole suite, which would
# otherwise take priority over both env_file=None and .env.example and make these tests
# pass for the wrong reason.
pytestmark = pytest.mark.usefixtures("clean_env")


def test_cors_origins_defaults_to_empty() -> None:
    """Fail closed: forgetting CORS_ORIGINS must allow nothing, not localhost."""
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
    """A typo here would otherwise sit dormant until the first booking was read."""
    monkeypatch.setenv("BOOKING_TIMEZONE", "Mars/Olympus")

    with pytest.raises(ValidationError):
        IsolatedSettings()
