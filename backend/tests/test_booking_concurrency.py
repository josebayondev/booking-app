"""Prueba de concurrencia real del EXCLUDE anti doble-reserva.

Los tests de test_models_domain.py demuestran que la restricción existe -- dos flushes
seguidos en la misma sesión, uno tras otro. Eso no dice nada sobre lo que de verdad
importa: dos peticiones HTTP concurrentes llegando al INSERT casi al mismo tiempo, cada
una en su propia transacción. Ninguna comprobación en Python (un SELECT antes del INSERT)
cierra esa ventana de carrera; solo una restricción que vive en la base de datos lo hace.
Este test reproduce esa carrera con dos conexiones reales y separadas.

No usa la fixture db_session -- su savepoint que se deshace al final sirve para aislar
tests entre sí, pero aquí el punto es justo lo contrario: cada hilo necesita una
transacción propia que compita de verdad contra la otra, así que ambas comprometen
(commit) de verdad y el propio test limpia lo que crea.
"""

import threading
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models import AppointmentType, Booking


@pytest.mark.db
def test_concurrent_overlapping_bookings_only_one_wins(_migrated_schema: None) -> None:
    from app.core.db import engine

    session_factory = sessionmaker(bind=engine)
    starts_at = datetime(2031, 3, 10, 10, 0, tzinfo=UTC)
    ends_at = datetime(2031, 3, 10, 10, 30, tzinfo=UTC)

    setup_session = session_factory()
    appointment_type = AppointmentType(
        slug="concurrency-test", name="Concurrencia", duration_minutes=30
    )
    setup_session.add(appointment_type)
    setup_session.commit()
    appointment_type_id = appointment_type.id
    setup_session.close()

    outcomes: dict[str, BaseException | None] = {}
    barrier = threading.Barrier(2)

    def attempt(label: str) -> None:
        session = session_factory()
        try:
            # Las dos peticiones esperan aquí a que la otra esté lista, para que el
            # INSERT no llegue antes por simple orden de arranque del hilo, sino que las
            # dos compitan de verdad por el mismo hueco.
            barrier.wait(timeout=5)
            session.add(
                Booking(
                    appointment_type_id=appointment_type_id,
                    customer_name="Cliente concurrente",
                    customer_email="concurrencia@example.com",
                    starts_at=starts_at,
                    ends_at=ends_at,
                )
            )
            session.commit()
            outcomes[label] = None
        except BaseException as exc:
            session.rollback()
            outcomes[label] = exc
        finally:
            session.close()

    try:
        threads = [
            threading.Thread(target=attempt, args=("a",)),
            threading.Thread(target=attempt, args=("b",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        successes = [outcome for outcome in outcomes.values() if outcome is None]
        failures = [outcome for outcome in outcomes.values() if outcome is not None]

        # Exactamente una gana el hueco. La otra bloquea hasta que la primera hace
        # commit, y entonces sí revienta contra el EXCLUDE -- eso es lo que demuestra que
        # la restricción resuelve la carrera y no solo la detecta a posteriori.
        assert len(successes) == 1
        assert len(failures) == 1
        assert isinstance(failures[0], IntegrityError)
    finally:
        # commit de verdad, no un rollback de savepoint: hay que borrar a mano lo que
        # este test deja escrito.
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM booking WHERE appointment_type_id = :id"),
                {"id": appointment_type_id},
            )
            connection.execute(
                text("DELETE FROM appointment_type WHERE id = :id"),
                {"id": appointment_type_id},
            )
