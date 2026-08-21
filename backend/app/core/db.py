"""Motor SQLAlchemy, fábrica de sesiones y comprobación de conexión al arrancar.

Aquí vive la única conexión a Postgres del backend: el `engine`, el `SessionLocal` del
que salen todas las sesiones, la dependencia `get_db()` para usar con `Depends()` y el
chequeo que main.py ejecuta en el lifespan para no arrancar contra una base caída.
"""

import logging
import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Esperas entre los intentos de conexión del arranque, en segundos. Neon suspende el
# cómputo inactivo, así que la primera conexión de un despliegue puede caer justo
# mientras se está despertando.
STARTUP_RETRY_DELAYS = (1.0, 2.0, 4.0)

engine = create_engine(
    make_url(settings.database_url).set(drivername="postgresql+psycopg"),
    pool_pre_ping=True,
    # Sin esto, una base de datos colgada bloquea el arranque indefinidamente, hasta que
    # expira la ventana de 15 minutos del health check de Render. Diez segundos fallan lo
    # bastante rápido como para que merezca la pena reintentar.
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> None:
    """Comprueba que la base de datos responde, reintentando por si sigue despertando.

    Relanza el último error cuando se agotan los reintentos: si la base es realmente
    inalcanzable, lo correcto es que el despliegue falle. Render mantiene sirviendo la
    versión anterior, así que un despliegue en rojo no es una caída del servicio.
    """
    attempts = len(STARTUP_RETRY_DELAYS) + 1

    for attempt, delay in enumerate((*STARTUP_RETRY_DELAYS, None), start=1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            if delay is None:
                logger.error("Database unreachable after %d attempts", attempts)
                raise
            logger.warning(
                "Database connection failed (attempt %d/%d), retrying in %.0fs: %s",
                attempt,
                attempts,
                delay,
                exc,
            )
            time.sleep(delay)
        else:
            logger.info("Database connection OK")
            return
