"""Tests de los reintentos de conexión al arrancar: Neon puede estar despertando, pero una
base realmente inalcanzable tiene que tumbar el despliegue."""

import logging

import pytest
from sqlalchemy.exc import OperationalError

from app.core import db

# No es un test puramente unitario: el camino feliz del test de reintentos deja que el
# segundo intento llegue al engine.connect() real.
pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _no_sleeping(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evita que la espera entre reintentos retrase de verdad la suite."""
    monkeypatch.setattr(db.time, "sleep", lambda _seconds: None)


def _boom() -> OperationalError:
    return OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_retries_until_the_database_answers(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Neon suspende el cómputo inactivo, así que el primer intento de un despliegue puede
    fallar."""
    attempts = {"n": 0}
    real_connect = db.engine.connect

    def flaky():  # type: ignore[no-untyped-def]
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise _boom()
        return real_connect()

    monkeypatch.setattr(db.engine, "connect", flaky)

    with caplog.at_level(logging.INFO):
        db.check_db_connection()

    assert attempts["n"] == 2
    assert "retrying" in caplog.text
    assert "Database connection OK" in caplog.text


def test_raises_once_the_retries_run_out(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Una base de datos realmente inalcanzable tiene que seguir tumbando el despliegue."""
    attempts = {"n": 0}

    def always_fails():  # type: ignore[no-untyped-def]
        attempts["n"] += 1
        raise _boom()

    monkeypatch.setattr(db.engine, "connect", always_fails)

    with caplog.at_level(logging.ERROR), pytest.raises(OperationalError):
        db.check_db_connection()

    assert attempts["n"] == len(db.STARTUP_RETRY_DELAYS) + 1
    assert "Database unreachable" in caplog.text
