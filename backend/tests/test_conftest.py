"""Tests del propio aislamiento de la suite: que no se lee ningún .env, que Sentry es
inalcanzable y que la sesión transaccional deshace de verdad lo que escribe un test."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core import config
from app.core.config import get_settings
from tests.conftest import transactional_session

BACKEND_DIR = Path(__file__).resolve().parent.parent
DOTENV = BACKEND_DIR / ".env"


def _dotenv_database_url() -> str | None:
    for line in DOTENV.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("DATABASE_URL="):
            return stripped.removeprefix("DATABASE_URL=").strip().strip("\"'")
    return None


def test_the_suite_reads_no_dotenv_file() -> None:
    """conftest.py vacía ENV_FILE antes de que se importe nunca app.core.config."""
    assert config._ENV_FILE is None


@pytest.mark.skipif(not DOTENV.exists(), reason="no hay .env local al que hacer sombra (CI)")
def test_settings_ignore_the_developers_dotenv() -> None:
    """La regresión por la que existe todo este montaje: backend/.env nombra la rama de
    desarrollo de Neon, y pytest se conectaba a ella salvo que prefijases DATABASE_URL a
    mano."""
    configured = _dotenv_database_url()

    assert configured, ".env existe pero no declara DATABASE_URL, revisa este test"
    assert get_settings().database_url != configured


def test_sentry_is_unreachable_from_the_suite() -> None:
    """Un SENTRY_DSN exportado no puede permitir que una ejecución de tests llegue al
    proyecto real."""
    assert not get_settings().sentry_dsn


@pytest.mark.db
def test_db_session_rolls_back_even_after_commit() -> None:
    """Comprobado desde fuera del context manager, así que demuestra que el desmontaje
    deshizo la escritura y no que la escritura no fuese visible nunca."""
    from app.core.db import engine

    with transactional_session() as session:
        session.execute(text("CREATE TABLE conftest_probe (id integer)"))
        session.execute(text("INSERT INTO conftest_probe VALUES (1)"))
        session.commit()

        assert session.execute(text("SELECT count(*) FROM conftest_probe")).scalar_one() == 1

    with engine.connect() as connection:
        survived = connection.execute(text("SELECT to_regclass('conftest_probe')")).scalar_one()

    assert survived is None


def test_client_does_not_open_a_database_connection(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    """La fixture client se salta el lifespan a propósito: la mayoría de tests necesitan la
    app, no una base de datos, y CI no debería ir más lento esperando a una."""
    from app.core import db

    def explode() -> None:
        raise AssertionError(
            "el lifespan se ejecutó, así que la fixture client tocó la base de datos"
        )

    monkeypatch.setattr(db, "check_db_connection", explode)

    assert client.get("/health").status_code == 200
