"""Tests de los modelos de dominio contra Postgres de verdad: persistencia, valores por
defecto que pone la base de datos y cada una de las restricciones."""

from datetime import UTC, datetime, time

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import AppointmentType, AvailabilityException, AvailabilityRule, Base, Booking


def test_every_domain_table_is_registered() -> None:
    """Caza el fallo que si no es silencioso: un modelo cuyo módulo nadie importa en
    app/models/__init__.py es invisible para el autogenerate de alembic, que entonces
    escribe una migración vacía y no dice nada."""
    assert set(Base.metadata.tables) == {
        "appointment_type",
        "availability_rule",
        "availability_exception",
        "booking",
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


def _booking(appointment_type_id: int, **overrides: object) -> Booking:
    defaults: dict[str, object] = {
        "appointment_type_id": appointment_type_id,
        "customer_name": "Ada Lovelace",
        "customer_email": "ada@example.com",
        "starts_at": datetime(2026, 8, 17, 10, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 8, 17, 10, 30, tzinfo=UTC),
    }
    return Booking(**(defaults | overrides))


@pytest.mark.db
class TestPersistence:
    def test_appointment_type_round_trips_with_its_defaults(self, db_session: Session) -> None:
        db_session.add(_appointment_type())
        db_session.flush()
        db_session.expire_all()

        stored = db_session.scalars(select(AppointmentType)).one()

        assert stored.slug == "reunion-inicial"
        assert stored.duration_minutes == 30
        # Los rellena la base de datos, no Python: una fila insertada desde psql también
        # los recibe.
        assert stored.buffer_minutes == 15
        assert stored.min_notice_hours == 12
        assert stored.max_advance_days == 60
        assert stored.is_active is True
        assert stored.sort_order == 0
        assert stored.description is None
        assert stored.created_at is not None
        assert stored.updated_at is not None

    def test_availability_exception_defaults_to_a_block(self, db_session: Session) -> None:
        """Una fila creada sin decir en qué dirección va tiene que cerrar el calendario, no
        abrirlo: olvidarse del flag debe fallar cerrado."""
        db_session.add(_exception())
        db_session.flush()
        db_session.expire_all()

        stored = db_session.scalars(select(AvailabilityException)).one()

        assert stored.is_available is False
        assert stored.reason is None

    def test_the_two_time_columns_keep_their_different_types(self, db_session: Session) -> None:
        """La piedra angular de todo el diseño, comprobada contra el propio Postgres y no
        contra SQLAlchemy: una regla es un reloj de pared naive, una excepción es un instante
        real.

        Si TIME llegase a ser TIMESTAMPTZ, "los lunes a las 10:00" pasaría a significar las
        11:00 cada verano, y nada más en la suite se enteraría.
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

    def test_booking_round_trips_with_its_defaults(self, db_session: Session) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()

        db_session.add(_booking(appointment_type.id))
        db_session.flush()
        db_session.expire_all()

        stored = db_session.scalars(select(Booking)).one()

        assert stored.status == "confirmed"
        # Generados por Python (default=), no por la base de datos: token_urlsafe y la
        # referencia con prefijo BK- no tienen equivalente en server_default.
        assert len(stored.token) == 43
        assert stored.reference.startswith("BK-")
        assert len(stored.reference) == 9
        assert stored.created_at is not None


@pytest.mark.db
class TestConstraints:
    """Una restricción por test. db_session deshace su transacción después, así que da igual
    que un flush fallido deje la sesión inservible."""

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
        """Lo que descarta también un bloque que cruce la medianoche."""
        db_session.add(_rule(ends_at_local=end))

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_rule_weekday_and_start_are_unique_together(self, db_session: Session) -> None:
        """La clave natural en la que se apoya el seed para insertar solo lo que falta."""
        db_session.add_all([_rule(), _rule(ends_at_local=time(13, 0))])

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_two_blocks_on_the_same_day_are_allowed(self, db_session: Session) -> None:
        """La otra cara de esa restricción: mañanas y tardes tienen que poder convivir."""
        db_session.add_all([_rule(), _rule(starts_at_local=time(16, 0), ends_at_local=time(19, 0))])

        db_session.flush()

    def test_exception_must_end_after_it_starts(self, db_session: Session) -> None:
        db_session.add(_exception(ends_at=datetime(2026, 8, 15, 0, 0, tzinfo=UTC)))

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_booking_requires_an_existing_appointment_type(self, db_session: Session) -> None:
        db_session.add(_booking(appointment_type_id=999))

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_booking_status_is_restricted(self, db_session: Session) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()

        db_session.add(_booking(appointment_type.id, status="pending"))

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_booking_must_end_after_it_starts(self, db_session: Session) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()

        db_session.add(
            _booking(
                appointment_type.id,
                starts_at=datetime(2026, 8, 17, 10, 0, tzinfo=UTC),
                ends_at=datetime(2026, 8, 17, 9, 0, tzinfo=UTC),
            )
        )

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_booking_token_is_unique(self, db_session: Session) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()

        shared_token = "a" * 43
        db_session.add_all(
            [
                _booking(appointment_type.id, token=shared_token),
                _booking(
                    appointment_type.id,
                    token=shared_token,
                    starts_at=datetime(2026, 8, 18, 10, 0, tzinfo=UTC),
                    ends_at=datetime(2026, 8, 18, 10, 30, tzinfo=UTC),
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_booking_reference_is_unique(self, db_session: Session) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()

        db_session.add_all(
            [
                _booking(appointment_type.id, reference="BK-111111"),
                _booking(
                    appointment_type.id,
                    reference="BK-111111",
                    starts_at=datetime(2026, 8, 18, 10, 0, tzinfo=UTC),
                    ends_at=datetime(2026, 8, 18, 10, 30, tzinfo=UTC),
                ),
            ]
        )

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_overlapping_bookings_are_rejected(self, db_session: Session) -> None:
        """La restricción que de verdad impide la doble reserva, contra Postgres y no
        solo contra la aplicación."""
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()

        db_session.add(_booking(appointment_type.id))
        db_session.flush()

        db_session.add(
            _booking(
                appointment_type.id,
                starts_at=datetime(2026, 8, 17, 10, 15, tzinfo=UTC),
                ends_at=datetime(2026, 8, 17, 10, 45, tzinfo=UTC),
            )
        )

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_a_cancelled_booking_frees_its_slot(self, db_session: Session) -> None:
        """La otra cara del EXCLUDE: cancelar tiene que liberar de verdad el hueco, no
        solo dejar de mostrarlo."""
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()

        db_session.add(_booking(appointment_type.id, status="cancelled"))
        db_session.flush()

        db_session.add(_booking(appointment_type.id))

        db_session.flush()

    def test_back_to_back_bookings_are_allowed(self, db_session: Session) -> None:
        """El rango es half-open ([)): que una reserva termine a las 10:30 justo cuando
        otra empieza no cuenta como solape."""
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()

        db_session.add(_booking(appointment_type.id))
        db_session.flush()

        db_session.add(
            _booking(
                appointment_type.id,
                starts_at=datetime(2026, 8, 17, 10, 30, tzinfo=UTC),
                ends_at=datetime(2026, 8, 17, 11, 0, tzinfo=UTC),
            )
        )

        db_session.flush()
