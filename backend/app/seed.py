"""La configuración inicial que necesita cualquier entorno antes de poder aceptar una reserva.

Se ejecuta con `uv run python -m app.seed`. Es idempotente, así que volver a lanzarlo es
seguro, y .github/workflows/migrate-production.yml lo corre justo después de
`alembic upgrade head` exactamente por eso: un entorno migrado pero sin sembrar
respondería a GET /availability con una lista vacía y parecería roto en vez de cerrado.

Los valores de aquí son valores *iniciales*, no impuestos -- ver seed_defaults().
"""

import logging
from datetime import time
from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AppointmentType, AvailabilityRule

logger = logging.getLogger(__name__)


class AppointmentTypeDefaults(NamedTuple):
    slug: str
    name: str
    description: str
    duration_minutes: int
    buffer_minutes: int
    min_notice_hours: int
    max_advance_days: int


class AvailabilityRuleDefaults(NamedTuple):
    weekday: int
    starts_at_local: time
    ends_at_local: time


# Un solo tipo por ahora. La API dejará el campo opcional y caerá al único tipo activo,
# así que añadir un segundo más adelante no cambia ningún contrato.
DEFAULT_APPOINTMENT_TYPES: tuple[AppointmentTypeDefaults, ...] = (
    AppointmentTypeDefaults(
        slug="reunion-inicial",
        name="Reunión inicial",
        description="Una primera videollamada para conocer tu proyecto y ver cómo puedo ayudarte.",
        duration_minutes=30,
        buffer_minutes=15,
        min_notice_hours=12,
        max_advance_days=60,
    ),
)

# De lunes a viernes, dos bloques al día, en hora de pared de Europe/Madrid. Diez filas.
_WORKDAYS = range(5)  # 0 = lunes, igual que date.weekday()
_DAILY_BLOCKS = ((time(10, 0), time(14, 0)), (time(16, 0), time(19, 0)))

DEFAULT_AVAILABILITY_RULES: tuple[AvailabilityRuleDefaults, ...] = tuple(
    AvailabilityRuleDefaults(weekday=weekday, starts_at_local=start, ends_at_local=end)
    for weekday in _WORKDAYS
    for start, end in _DAILY_BLOCKS
)


def seed_defaults(session: Session) -> int:
    """Inserta las filas por defecto que falten. Devuelve cuántas ha creado.

    Idempotente por clave natural: los tipos de cita por slug, las reglas de
    disponibilidad por (weekday, starts_at_local) -- los mismos pares sobre los que están
    construidas las restricciones únicas.

    Deliberadamente **no actualiza las filas que ya existen**. Una vez que la duración se
    cambia a 45 minutos desde el panel de administración, o que se borra un viernes por la
    tarde, el siguiente despliegue no puede volver a ponerlo. Estos son los valores desde
    los que arranca una base de datos nueva, no valores que esta función mantenga a la
    fuerza.

    No hace commit: decide quien llama. Eso es lo que permite a los tests ejecutarlo dentro
    de la transacción del fixture db_session y que se deshaga después.
    """
    created = 0

    for defaults in DEFAULT_APPOINTMENT_TYPES:
        exists = session.scalar(
            select(AppointmentType.id).where(AppointmentType.slug == defaults.slug)
        )
        if exists is None:
            session.add(AppointmentType(**defaults._asdict()))
            created += 1
            logger.info("Seeding appointment type %s", defaults.slug)

    for rule in DEFAULT_AVAILABILITY_RULES:
        exists = session.scalar(
            select(AvailabilityRule.id).where(
                AvailabilityRule.weekday == rule.weekday,
                AvailabilityRule.starts_at_local == rule.starts_at_local,
            )
        )
        if exists is None:
            session.add(AvailabilityRule(**rule._asdict()))
            created += 1
            logger.info(
                "Seeding availability rule: weekday %d at %s", rule.weekday, rule.starts_at_local
            )

    session.flush()
    return created


def main() -> None:
    # Importado aquí y no a nivel de módulo para que importar app.seed -- cosa que hacen
    # los tests -- no construya un engine como efecto colateral.
    from app.core.db import SessionLocal

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with SessionLocal() as session:
        created = seed_defaults(session)
        session.commit()

    logger.info("Seed complete: %d row(s) created, existing rows left untouched.", created)


if __name__ == "__main__":
    main()
