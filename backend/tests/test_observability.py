import logging
from typing import Any

import pytest
import sentry_sdk
from pydantic_settings import SettingsConfigDict
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import Settings
from app.core.observability import configure_sentry

DSN = "https://public@o0.ingest.sentry.io/0"


class IsolatedSettings(Settings):
    """Ignores any local .env so these tests only see what they set themselves."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


@pytest.fixture
def init_kwargs(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Records what configure_sentry would pass to sentry_sdk.init."""
    recorded: list[dict[str, Any]] = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: recorded.append(kwargs))
    return recorded


def test_no_dsn_does_not_initialise_sentry(init_kwargs: list[dict[str, Any]]) -> None:
    configure_sentry(IsolatedSettings())

    assert init_kwargs == []


def test_empty_dsn_does_not_initialise_sentry(init_kwargs: list[dict[str, Any]]) -> None:
    configure_sentry(IsolatedSettings(sentry_dsn=""))

    assert init_kwargs == []


def test_dsn_initialises_sentry_with_the_current_environment(
    init_kwargs: list[dict[str, Any]],
) -> None:
    configure_sentry(IsolatedSettings(sentry_dsn=DSN, environment="production"))

    assert len(init_kwargs) == 1
    assert init_kwargs[0]["dsn"] == DSN
    assert init_kwargs[0]["environment"] == "production"


def test_pii_is_never_sent(init_kwargs: list[dict[str, Any]]) -> None:
    """CLAUDE.md requires send_default_pii=False: bookings carry personal data."""
    configure_sentry(IsolatedSettings(sentry_dsn=DSN))

    assert init_kwargs[0]["send_default_pii"] is False


def test_logging_errors_are_reported_as_events(init_kwargs: list[dict[str, Any]]) -> None:
    configure_sentry(IsolatedSettings(sentry_dsn=DSN))

    integrations = init_kwargs[0]["integrations"]
    logging_integration = next(i for i in integrations if isinstance(i, LoggingIntegration))

    assert logging_integration._handler.level == logging.ERROR
