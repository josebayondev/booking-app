from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.timezone import local_to_utc
from app.models import AppointmentType, AvailabilityRule
from app.seed import DEFAULT_APPOINTMENT_TYPES, DEFAULT_AVAILABILITY_RULES, seed_defaults

# --------------------------------------------------------------------------------------
# The constants themselves. No database needed: these guard the values, not the writing.
# --------------------------------------------------------------------------------------


def test_the_default_schedule_is_ten_weekday_blocks() -> None:
    assert len(DEFAULT_AVAILABILITY_RULES) == 10
    assert {rule.weekday for rule in DEFAULT_AVAILABILITY_RULES} == {0, 1, 2, 3, 4}


def test_every_default_rule_would_satisfy_its_constraints() -> None:
    """Cheaper than finding out from an IntegrityError in a migration job."""
    for rule in DEFAULT_AVAILABILITY_RULES:
        assert 0 <= rule.weekday <= 6
        assert rule.ends_at_local > rule.starts_at_local


def test_default_rules_are_unique_by_their_natural_key() -> None:
    """If two defaults collided, the seed would fail on a fresh database -- and only
    there, since on a seeded one the duplicate would be skipped as already present."""
    keys = [(rule.weekday, rule.starts_at_local) for rule in DEFAULT_AVAILABILITY_RULES]

    assert len(set(keys)) == len(keys)


def test_there_is_exactly_one_default_appointment_type() -> None:
    """The API falls back to the single active type when the client names none. A second
    seeded type would not break that, but it would make the fallback ambiguous, so it is
    a deliberate decision rather than something to drift into."""
    assert len(DEFAULT_APPOINTMENT_TYPES) == 1
    assert DEFAULT_APPOINTMENT_TYPES[0].duration_minutes == 30
    assert DEFAULT_APPOINTMENT_TYPES[0].buffer_minutes >= 0


def test_every_default_block_fits_at_least_one_meeting() -> None:
    """A 30 minute meeting plus its 15 minute buffer has to fit inside every block, or
    that block would be seeded only to yield nothing. It does not have to divide evenly:
    a four hour block fits five meetings and leaves a stranded 15 minutes, which is
    correct -- the remainder is simply not offered."""
    appointment = DEFAULT_APPOINTMENT_TYPES[0]
    step = appointment.duration_minutes + appointment.buffer_minutes

    for rule in DEFAULT_AVAILABILITY_RULES:
        span = (
            rule.ends_at_local.hour * 60
            + rule.ends_at_local.minute
            - rule.starts_at_local.hour * 60
            - rule.starts_at_local.minute
        )
        assert span >= step


def test_the_schedule_survives_the_change_of_clocks() -> None:
    """Ties the seed to app/core/timezone.py. 10:00 Madrid is 09:00Z in winter and
    08:00Z in summer -- the same wall clock, two different instants. That is the entire
    reason the rule stores a naive TIME.
    """
    morning = DEFAULT_AVAILABILITY_RULES[0].starts_at_local

    winter = local_to_utc(date(2026, 1, 5), morning)  # a Monday
    summer = local_to_utc(date(2026, 7, 6), morning)  # a Monday

    assert (winter.hour, winter.minute) == (9, 0)
    assert (summer.hour, summer.minute) == (8, 0)


# --------------------------------------------------------------------------------------
# Writing them.
# --------------------------------------------------------------------------------------


def _counts(session: Session) -> tuple[int, int]:
    return (
        session.scalar(select(func.count()).select_from(AppointmentType)) or 0,
        session.scalar(select(func.count()).select_from(AvailabilityRule)) or 0,
    )


@pytest.mark.db
def test_seeding_an_empty_database_creates_every_default(db_session: Session) -> None:
    created = seed_defaults(db_session)

    assert created == len(DEFAULT_APPOINTMENT_TYPES) + len(DEFAULT_AVAILABILITY_RULES)
    assert _counts(db_session) == (1, 10)


@pytest.mark.db
def test_seeding_twice_changes_nothing(db_session: Session) -> None:
    """The property the CI step depends on: migrate-production.yml runs this on every
    push touching the seed, so a second run must be a no-op."""
    seed_defaults(db_session)
    before = _counts(db_session)

    created = seed_defaults(db_session)

    assert created == 0
    assert _counts(db_session) == before


@pytest.mark.db
def test_seeding_does_not_overwrite_edited_values(db_session: Session) -> None:
    """These are the values a fresh database starts from, not values the seed keeps
    enforcing. Once the duration is changed from the admin panel, redeploying must not
    put 30 minutes back.
    """
    seed_defaults(db_session)
    stored = db_session.scalars(select(AppointmentType)).one()
    stored.duration_minutes = 45
    stored.name = "Sesión técnica"
    db_session.flush()

    seed_defaults(db_session)
    db_session.expire_all()

    edited = db_session.scalars(select(AppointmentType)).one()
    assert edited.duration_minutes == 45
    assert edited.name == "Sesión técnica"


@pytest.mark.db
def test_a_deleted_rule_comes_back(db_session: Session) -> None:
    """The other side of the same coin, and the reason the seed is not simply skipped
    when the table is non-empty: a row that is missing by its natural key is missing,
    whether it was never created or deleted by hand."""
    seed_defaults(db_session)
    db_session.delete(db_session.scalars(select(AvailabilityRule)).first())
    db_session.flush()

    assert seed_defaults(db_session) == 1
    assert _counts(db_session) == (1, 10)
