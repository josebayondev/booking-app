"""The initial configuration every environment needs before it can take a booking.

Run it with `uv run python -m app.seed`. It is idempotent, so running it again is safe,
and .github/workflows/migrate-production.yml runs it right after `alembic upgrade head`
for exactly that reason: an environment that migrated but was never seeded would answer
GET /availability with an empty list and look broken rather than closed.

The values here are *initial* values, not enforced ones -- see seed_defaults().
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


# One type for now. The API will leave the field optional and fall back to the single
# active type, so adding a second one later changes no contract.
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

# Monday to Friday, two blocks a day, in Europe/Madrid wall-clock time. Ten rows.
_WORKDAYS = range(5)  # 0 = Monday, matching date.weekday()
_DAILY_BLOCKS = ((time(10, 0), time(14, 0)), (time(16, 0), time(19, 0)))

DEFAULT_AVAILABILITY_RULES: tuple[AvailabilityRuleDefaults, ...] = tuple(
    AvailabilityRuleDefaults(weekday=weekday, starts_at_local=start, ends_at_local=end)
    for weekday in _WORKDAYS
    for start, end in _DAILY_BLOCKS
)


def seed_defaults(session: Session) -> int:
    """Insert whatever default rows are missing. Returns how many were created.

    Idempotent by natural key: appointment types by slug, availability rules by
    (weekday, starts_at_local) -- the same pairs the unique constraints are built on.

    It deliberately **does not update rows that already exist**. Once the duration is
    changed to 45 minutes from the admin panel, or a Friday afternoon is deleted, the
    next deploy must not put it back. These are the values a fresh database starts from,
    not values this function keeps enforcing.

    Does not commit: the caller decides. That is what lets the tests run it inside the
    db_session fixture's transaction and have it rolled back.
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
    # Imported here and not at module level so that importing app.seed -- which the
    # tests do -- never builds an engine as a side effect.
    from app.core.db import SessionLocal

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with SessionLocal() as session:
        created = seed_defaults(session)
        session.commit()

    logger.info("Seed complete: %d row(s) created, existing rows left untouched.", created)


if __name__ == "__main__":
    main()
