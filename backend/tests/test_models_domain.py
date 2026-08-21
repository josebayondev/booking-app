from datetime import UTC, datetime, time

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AppointmentType, AvailabilityException, AvailabilityRule, Base


def test_every_domain_table_is_registered() -> None:
    """Catches the failure that is otherwise silent: a model whose module nobody
    imports in app/models/__init__.py is invisible to alembic autogenerate, which then
    writes an empty migration and says nothing."""
    assert set(Base.metadata.tables) == {
        "appointment_type",
        "availability_rule",
        "availability_exception",
    }


def _appointment_type(**overrides: object) -> AppointmentType:
    defaults: dict[str, object] = {
        "slug": "reunion-inicial",
        "name": "Reunión inicial",
        "duration_minutes": 30,
    }
    return AppointmentType(**(defaults | overrides))


def _rule(**overrides: object) -> AvailabilityRule:
    defaults: dict[str, object] = {
        "weekday": 0,
        "starts_at_local": time(10, 0),
        "ends_at_local": time(14, 0),
    }
    return AvailabilityRule(**(defaults | overrides))


def _exception(**overrides: object) -> AvailabilityException:
    defaults: dict[str, object] = {
        "starts_at": datetime(2026, 8, 15, 0, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 8, 16, 0, 0, tzinfo=UTC),
    }
    return AvailabilityException(**(defaults | overrides))


@pytest.mark.db
class TestPersistence:
    def test_appointment_type_round_trips_with_its_defaults(self, db_session: Session) -> None:
        db_session.add(_appointment_type())
        db_session.flush()
        db_session.expire_all()

        stored = db_session.scalars(select(AppointmentType)).one()

        assert stored.slug == "reunion-inicial"
        assert stored.duration_minutes == 30
        # Filled by the database, not by Python: a row inserted from psql gets them too.
        assert stored.buffer_minutes == 15
        assert stored.min_notice_hours == 12
        assert stored.max_advance_days == 60
        assert stored.is_active is True
        assert stored.sort_order == 0
        assert stored.description is None
        assert stored.created_at is not None
        assert stored.updated_at is not None

    def test_availability_exception_defaults_to_a_block(self, db_session: Session) -> None:
        """A row created without saying which way it goes must close the calendar, not
        open it: forgetting the flag has to fail closed."""
        db_session.add(_exception())
        db_session.flush()
        db_session.expire_all()

        stored = db_session.scalars(select(AvailabilityException)).one()

        assert stored.is_available is False
        assert stored.reason is None

    def test_the_two_time_columns_keep_their_different_types(self, db_session: Session) -> None:
        """The keystone of the whole design, asserted against Postgres itself rather than
        against SQLAlchemy: a rule is a naive wall clock, an exception is a real instant.

        If TIME ever became TIMESTAMPTZ, "Mondays at 10:00" would start meaning 11:00
        every summer, and nothing else in the suite would notice.
        """
        db_session.add_all([_rule(), _exception()])
        db_session.flush()
        db_session.expire_all()

        rule = db_session.scalars(select(AvailabilityRule)).one()
        exception = db_session.scalars(select(AvailabilityException)).one()

        assert rule.starts_at_local == time(10, 0)
        assert rule.starts_at_local.tzinfo is None
        assert exception.starts_at.tzinfo is not None
        assert exception.starts_at == datetime(2026, 8, 15, 0, 0, tzinfo=UTC)


@pytest.mark.db
class TestConstraints:
    """One constraint per test. db_session rolls its transaction back afterwards, so a
    failed flush leaving the session unusable does not matter."""

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("duration_minutes", 0),
            ("duration_minutes", 481),
            ("buffer_minutes", -1),
            ("min_notice_hours", -1),
            ("max_advance_days", 0),
            ("max_advance_days", 366),
        ],
    )
    def test_appointment_type_policy_ranges(
        self, db_session: Session, field: str, value: int
    ) -> None:
        db_session.add(_appointment_type(**{field: value}))

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_appointment_type_slug_is_unique(self, db_session: Session) -> None:
        db_session.add_all([_appointment_type(), _appointment_type(name="Otra")])

        with pytest.raises(IntegrityError):
            db_session.flush()

    @pytest.mark.parametrize("weekday", [-1, 7])
    def test_rule_weekday_must_be_a_weekday(self, db_session: Session, weekday: int) -> None:
        db_session.add(_rule(weekday=weekday))

        with pytest.raises(IntegrityError):
            db_session.flush()

    @pytest.mark.parametrize("end", [time(10, 0), time(9, 0)])
    def test_rule_must_end_after_it_starts(self, db_session: Session, end: time) -> None:
        """Which also rules out a block crossing midnight."""
        db_session.add(_rule(ends_at_local=end))

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_rule_weekday_and_start_are_unique_together(self, db_session: Session) -> None:
        """The natural key the seed relies on to insert only what is missing."""
        db_session.add_all([_rule(), _rule(ends_at_local=time(13, 0))])

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_two_blocks_on_the_same_day_are_allowed(self, db_session: Session) -> None:
        """The other side of that constraint: mornings and afternoons must coexist."""
        db_session.add_all([_rule(), _rule(starts_at_local=time(16, 0), ends_at_local=time(19, 0))])

        db_session.flush()

    def test_exception_must_end_after_it_starts(self, db_session: Session) -> None:
        db_session.add(_exception(ends_at=datetime(2026, 8, 15, 0, 0, tzinfo=UTC)))

        with pytest.raises(IntegrityError):
            db_session.flush()
