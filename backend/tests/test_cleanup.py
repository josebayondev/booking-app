"""Tests de app/cleanup.py: qué reservas borra la política de retención y cuáles no."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cleanup import RETENTION_DAYS, delete_past_bookings
from app.models import AppointmentType, Booking

_NOW = datetime(2027, 1, 1, tzinfo=UTC)


def _appointment_type() -> AppointmentType:
    return AppointmentType(
        slug="reunion-inicial",
        name="Reunión inicial",
        duration_minutes=30,
        buffer_minutes=0,
        min_notice_hours=0,
        max_advance_days=365,
        is_active=True,
        sort_order=0,
    )


def _booking(appointment_type_id: int, ends_at: datetime, **overrides: object) -> Booking:
    defaults: dict[str, object] = {
        "appointment_type_id": appointment_type_id,
        "customer_name": "Ada Lovelace",
        "customer_email": "ada@example.com",
        "starts_at": ends_at - timedelta(minutes=30),
        "ends_at": ends_at,
    }
    return Booking(**(defaults | overrides))


def _seed_type(session: Session) -> int:
    appointment_type = _appointment_type()
    session.add(appointment_type)
    session.flush()
    return appointment_type.id


def _count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Booking)) or 0


@pytest.mark.db
def test_deletes_a_booking_well_past_the_retention_window(db_session: Session) -> None:
    appointment_type_id = _seed_type(db_session)
    ends_at = _NOW - timedelta(days=RETENTION_DAYS + 30)
    db_session.add(_booking(appointment_type_id, ends_at=ends_at))
    db_session.flush()

    deleted = delete_past_bookings(db_session, now=_NOW)

    assert deleted == 1
    assert _count(db_session) == 0


@pytest.mark.db
def test_deletes_a_past_booking_regardless_of_status(db_session: Session) -> None:
    """La retención borra por antigüedad, no por si la reserva se llegó a cumplir."""
    appointment_type_id = _seed_type(db_session)
    db_session.add(
        _booking(
            appointment_type_id,
            ends_at=_NOW - timedelta(days=RETENTION_DAYS + 30),
            status="cancelled",
        )
    )
    db_session.flush()

    deleted = delete_past_bookings(db_session, now=_NOW)

    assert deleted == 1
    assert _count(db_session) == 0


@pytest.mark.db
def test_keeps_a_recent_or_future_booking(db_session: Session) -> None:
    appointment_type_id = _seed_type(db_session)
    recent = _booking(appointment_type_id, ends_at=_NOW - timedelta(days=1))
    future = _booking(
        appointment_type_id,
        ends_at=_NOW + timedelta(days=1),
        starts_at=_NOW + timedelta(hours=23, minutes=30),
    )
    db_session.add_all([recent, future])
    db_session.flush()

    deleted = delete_past_bookings(db_session, now=_NOW)

    assert deleted == 0
    assert _count(db_session) == 2


@pytest.mark.db
def test_a_booking_ending_exactly_at_the_cutoff_is_kept(db_session: Session) -> None:
    """El corte es estrictamente anterior al plazo: cumplirlo justo hoy no basta todavía."""
    appointment_type_id = _seed_type(db_session)
    db_session.add(
        _booking(
            appointment_type_id,
            ends_at=_NOW - timedelta(days=RETENTION_DAYS),
        )
    )
    db_session.flush()

    deleted = delete_past_bookings(db_session, now=_NOW)

    assert deleted == 0
    assert _count(db_session) == 1


@pytest.mark.db
def test_running_it_twice_the_second_pass_deletes_nothing(db_session: Session) -> None:
    appointment_type_id = _seed_type(db_session)
    db_session.add(_booking(appointment_type_id, ends_at=_NOW - timedelta(days=RETENTION_DAYS + 1)))
    db_session.flush()

    delete_past_bookings(db_session, now=_NOW)
    second_pass = delete_past_bookings(db_session, now=_NOW)

    assert second_pass == 0
