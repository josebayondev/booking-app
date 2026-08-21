"""Tests de la integración con Sentry y, sobre todo, del borrado de datos personales:
que un evento capturado de verdad no lleva ni un email ni un teléfono."""

import json
import logging
from collections.abc import Iterator
from typing import Any

import pytest
import sentry_sdk
from pydantic_settings import SettingsConfigDict
from sentry_sdk.envelope import Envelope
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.transport import Transport

from app.core.config import Settings
from app.core.observability import REDACTED, configure_sentry, scrub_event

DSN = "https://public@o0.ingest.sentry.io/0"


class IsolatedSettings(Settings):
    """Ignora cualquier .env local para que estos tests solo vean lo que ellos fijan."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


@pytest.fixture
def init_kwargs(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Registra lo que configure_sentry le pasaría a sentry_sdk.init."""
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
    """CLAUDE.md exige send_default_pii=False: las reservas llevan datos personales."""
    configure_sentry(IsolatedSettings(sentry_dsn=DSN))

    assert init_kwargs[0]["send_default_pii"] is False


def test_logging_errors_are_reported_as_events(init_kwargs: list[dict[str, Any]]) -> None:
    configure_sentry(IsolatedSettings(sentry_dsn=DSN))

    integrations = init_kwargs[0]["integrations"]
    logging_integration = next(i for i in integrations if isinstance(i, LoggingIntegration))

    assert logging_integration._handler.level == logging.ERROR


def test_invalid_dsn_does_not_kill_the_app(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """configure_sentry corre en tiempo de import: lanzar aquí mataría el contenedor."""

    def explode(**kwargs: Any) -> None:
        raise ValueError("Unsupported scheme ''")

    monkeypatch.setattr(sentry_sdk, "init", explode)

    with caplog.at_level(logging.ERROR):
        configure_sentry(IsolatedSettings(sentry_dsn="not-a-dsn"))

    assert "Sentry init failed" in caplog.text


def test_before_send_is_registered(init_kwargs: list[dict[str, Any]]) -> None:
    configure_sentry(IsolatedSettings(sentry_dsn=DSN))

    assert init_kwargs[0]["before_send"] is scrub_event


@pytest.mark.parametrize(
    ("message", "leak"),
    [
        ("booking failed for ana.lopez+test@example.com", "ana.lopez+test@example.com"),
        ("could not reach 612345678", "612345678"),
        ("could not reach +34 612 345 678", "612 345 678"),
    ],
    ids=["email", "phone", "phone-with-prefix"],
)
def test_free_text_pii_is_redacted(message: str, leak: str) -> None:
    """La fuga realista: datos personales interpolados en una línea de log, sin ninguna
    clave que sirva de pista."""
    event: Any = {"logentry": {"formatted": message}}

    scrubbed: Any = scrub_event(event, {})

    assert leak not in json.dumps(scrubbed)
    assert REDACTED in scrubbed["logentry"]["formatted"]


def test_sensitive_keys_are_redacted_whatever_the_value_looks_like() -> None:
    """Un teléfono guardado como "ext. 4" no encaja con ningún patrón, pero la clave lo
    delata."""
    event: Any = {"extra": {"customer_email": "not-an-email", "phone": "ext. 4"}}

    scrubbed: Any = scrub_event(event, {})

    assert scrubbed["extra"] == {"customer_email": REDACTED, "phone": REDACTED}


def test_pii_is_redacted_however_deeply_it_is_nested() -> None:
    """Sentry captura las variables locales de cada frame; ese es el escondite de verdad."""
    event: Any = {
        "exception": {
            "values": [
                {
                    "stacktrace": {
                        "frames": [{"vars": {"customer": "ana@example.com"}}],
                    }
                }
            ]
        },
        "breadcrumbs": {"values": [{"message": "sent to ana@example.com"}]},
    }

    dumped = json.dumps(scrub_event(event, {}))

    assert "ana@example.com" not in dumped
    assert dumped.count(REDACTED) == 2


def test_scrubbing_leaves_useful_debugging_data_alone() -> None:
    """Un patrón lo bastante laxo como para comerse ids y timestamps dejaría los eventos
    inservibles."""
    event: Any = {
        "event_id": "9f8e7d6c5b4a39281706f5e4d3c2b1a0",
        "timestamp": "1787215705368",
        "extra": {"hotel": "Ritz", "rows_scanned": 290664, "duration_ms": 1234567890123},
    }

    scrubbed: Any = scrub_event(event, {})

    assert scrubbed == event


def test_events_are_scrubbed_never_dropped() -> None:
    """Devolver None descartaría el informe en silencio en vez de limpiarlo."""
    assert scrub_event({"logentry": {"formatted": "boom"}}, {}) is not None


class RecordingTransport(Transport):
    """Guarda cada envelope en memoria en vez de enviarlo. Una subclase de Transport y no
    una función suelta: sentry-sdk dejó obsoletos los transportes en forma de función."""

    def __init__(self, events: list[dict[str, Any]]) -> None:
        super().__init__()
        self.events = events

    def capture_envelope(self, envelope: Envelope) -> None:
        event = envelope.get_event()
        if event is not None:
            self.events.append(dict(event))


@pytest.fixture
def sent_events(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[dict[str, Any]]]:
    """Inicializa Sentry exactamente igual que configure_sentry, pero nada sale del proceso:
    el transporte se limita a registrar lo que habría viajado por el cable."""
    events: list[dict[str, Any]] = []
    real_init = sentry_sdk.init

    def init_with_capturing_transport(**kwargs: Any) -> Any:
        return real_init(**kwargs, transport=RecordingTransport(events))

    monkeypatch.setattr(sentry_sdk, "init", init_with_capturing_transport)
    configure_sentry(IsolatedSettings(sentry_dsn=DSN, environment="production"))
    yield events
    sentry_sdk.get_client().close()


def test_dod_a_captured_event_carries_no_email_or_phone(
    sent_events: list[dict[str, Any]],
) -> None:
    """El DoD de ClickUp, de punta a punta: registrar un error como lo hace la app de verdad
    e inspeccionar el payload que Sentry habría transmitido."""
    logging.getLogger("app.test").error(
        "no se pudo confirmar la reserva de ana.lopez@example.com, tel 612345678"
    )
    sentry_sdk.get_client().flush()

    assert len(sent_events) == 1
    payload = json.dumps(sent_events[0])
    assert "ana.lopez@example.com" not in payload
    assert "612345678" not in payload
    assert REDACTED in payload
