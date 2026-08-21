"""Tests del seed: primero las constantes por defecto en sí, y después su escritura
idempotente contra la base de datos."""

from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.timezone import local_to_utc
from app.models import AppointmentType, AvailabilityRule
from app.seed import DEFAULT_APPOINTMENT_TYPES, DEFAULT_AVAILABILITY_RULES, seed_defaults

# --------------------------------------------------------------------------------------
# Las constantes en sí. No hace falta base de datos: esto vigila los valores, no la
# escritura.
# --------------------------------------------------------------------------------------


def test_the_default_schedule_is_ten_weekday_blocks() -> None:
    assert len(DEFAULT_AVAILABILITY_RULES) == 10
    assert {rule.weekday for rule in DEFAULT_AVAILABILITY_RULES} == {0, 1, 2, 3, 4}


def test_every_default_rule_would_satisfy_its_constraints() -> None:
    """Más barato que enterarse por un IntegrityError en el job de migraciones."""
    for rule in DEFAULT_AVAILABILITY_RULES:
        assert 0 <= rule.weekday <= 6
        assert rule.ends_at_local > rule.starts_at_local


def test_default_rules_are_unique_by_their_natural_key() -> None:
    """Si dos valores por defecto colisionasen, el seed fallaría en una base de datos nueva
    -- y solo ahí, porque en una ya sembrada el duplicado se saltaría por existente."""
    keys = [(rule.weekday, rule.starts_at_local) for rule in DEFAULT_AVAILABILITY_RULES]

    assert len(set(keys)) == len(keys)


def test_there_is_exactly_one_default_appointment_type() -> None:
    """La API cae al único tipo activo cuando el cliente no nombra ninguno. Un segundo tipo
    sembrado no rompería eso, pero haría ambigua esa caída, así que es una decisión
    deliberada y no algo hacia lo que dejarse llevar."""
    assert len(DEFAULT_APPOINTMENT_TYPES) == 1
    assert DEFAULT_APPOINTMENT_TYPES[0].duration_minutes == 30
    assert DEFAULT_APPOINTMENT_TYPES[0].buffer_minutes >= 0


def test_every_default_block_fits_at_least_one_meeting() -> None:
    """Una reunión de 30 minutos más su colchón de 15 tiene que caber en todos los bloques,
    o ese bloque se sembraría solo para no dar nada. No hace falta que divida exacto: un
    bloque de cuatro horas da para cinco reuniones y deja 15 minutos sueltos, que es lo
    correcto -- ese resto simplemente no se ofrece."""
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
    """Ata el seed a app/core/timezone.py. Las 10:00 de Madrid son las 09:00Z en invierno y
    las 08:00Z en verano -- el mismo reloj de pared, dos instantes distintos. Esa es toda la
    razón de que la regla guarde un TIME naive.
    """
    morning = DEFAULT_AVAILABILITY_RULES[0].starts_at_local

    winter = local_to_utc(date(2026, 1, 5), morning)  # un lunes
    summer = local_to_utc(date(2026, 7, 6), morning)  # un lunes

    assert (winter.hour, winter.minute) == (9, 0)
    assert (summer.hour, summer.minute) == (8, 0)


# --------------------------------------------------------------------------------------
# Y ahora, escribirlas.
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
    """La propiedad de la que depende el paso de CI: migrate-production.yml lo ejecuta en
    cada push que toque el seed, así que una segunda pasada tiene que ser un no-op."""
    seed_defaults(db_session)
    before = _counts(db_session)

    created = seed_defaults(db_session)

    assert created == 0
    assert _counts(db_session) == before


@pytest.mark.db
def test_seeding_does_not_overwrite_edited_values(db_session: Session) -> None:
    """Estos son los valores desde los que arranca una base de datos nueva, no valores que
    el seed mantenga a la fuerza. Una vez cambiada la duración desde el panel de
    administración, redesplegar no puede volver a poner 30 minutos.
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
    """La otra cara de la misma moneda, y el motivo de que el seed no se salte sin más
    cuando la tabla no está vacía: una fila que falta por su clave natural es una fila que
    falta, la creasen nunca o la borrasen a mano."""
    seed_defaults(db_session)
    db_session.delete(db_session.scalars(select(AvailabilityRule)).first())
    db_session.flush()

    assert seed_defaults(db_session) == 1
    assert _counts(db_session) == (1, 10)
