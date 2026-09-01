"""Tests de las rutas de app/api/bookings.py, contra Postgres de verdad.

Usan api_client (tests/conftest.py), no client: el endpoint necesita ver dentro de la
misma transacción las filas que cada test prepara con db_session.
"""

from datetime import UTC, date, datetime, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AppointmentType, AvailabilityRule, Booking


def _appointment_type(**overrides: object) -> AppointmentType:
    defaults: dict[str, object] = {
        "slug": "reunion-inicial",
        "name": "Reunión inicial",
        "duration_minutes": 30,
        "buffer_minutes": 0,
        "min_notice_hours": 0,
        "max_advance_days": 365,
        "is_active": True,
        "sort_order": 0,
    }
    return AppointmentType(**(defaults | overrides))


def _rule(**overrides: object) -> AvailabilityRule:
    defaults: dict[str, object] = {
        "weekday": date(2026, 9, 7).weekday(),  # lunes
        "starts_at_local": time(10, 0),
        "ends_at_local": time(14, 0),
        "is_active": True,
    }
    return AvailabilityRule(**(defaults | overrides))


# 10:00 en Madrid es verano (CEST, UTC+2) -> 08:00Z. Primer slot libre de _rule().
_FREE_SLOT_STARTS_AT = "2026-09-07T08:00:00Z"
# Otro slot libre del mismo día (10:30-11:00 Madrid), para reprogramar sin chocar.
_OTHER_FREE_SLOT_STARTS_AT = "2026-09-07T08:30:00Z"


def _payload(**overrides: object) -> dict[str, object]:
    defaults: dict[str, object] = {
        "type": "reunion-inicial",
        "starts_at": _FREE_SLOT_STARTS_AT,
        "customer_name": "Ada Lovelace",
        "customer_email": "ada@example.com",
    }
    return defaults | overrides


def _booking(appointment_type_id: int, **overrides: object) -> Booking:
    defaults: dict[str, object] = {
        "appointment_type_id": appointment_type_id,
        "customer_name": "Ada Lovelace",
        "customer_email": "ada@example.com",
        "starts_at": datetime(2026, 9, 7, 8, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 9, 7, 8, 30, tzinfo=UTC),
    }
    return Booking(**(defaults | overrides))


@pytest.mark.db
class TestCreateBooking:
    def test_books_a_free_slot(self, db_session: Session, api_client: TestClient) -> None:
        db_session.add(_appointment_type())
        db_session.add(_rule())
        db_session.flush()

        response = api_client.post("/api/v1/bookings", json=_payload())

        assert response.status_code == 201
        body = response.json()
        assert body["starts_at"] == "2026-09-07T08:00:00Z"
        assert body["ends_at"] == "2026-09-07T08:30:00Z"
        assert body["token"]
        assert body["reference"].startswith("BK-")
        assert response.headers["location"] == f"/api/v1/bookings/{body['token']}"

    def test_double_booking_the_same_slot_returns_409_not_500(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        db_session.add(_appointment_type())
        db_session.add(_rule())
        db_session.flush()

        first = api_client.post("/api/v1/bookings", json=_payload())
        assert first.status_code == 201

        second = api_client.post("/api/v1/bookings", json=_payload())

        assert second.status_code == 409
        assert second.json() == {
            "code": "slot_unavailable",
            "detail": "Ese horario ya no está disponible.",
        }

    def test_returns_404_for_an_unknown_slug(self, api_client: TestClient) -> None:
        response = api_client.post("/api/v1/bookings", json=_payload(type="no-existe"))

        assert response.status_code == 404
        assert response.json()["code"] == "appointment_type_not_found"

    def test_rejects_an_instant_outside_any_free_slot(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        db_session.add(_appointment_type())
        db_session.add(_rule())
        db_session.flush()

        response = api_client.post(
            "/api/v1/bookings",
            json=_payload(starts_at="2026-09-07T23:00:00Z"),  # fuera de 10:00-14:00 Madrid
        )

        assert response.status_code == 409
        assert response.json()["code"] == "slot_unavailable"

    def test_rejects_a_naive_starts_at(self, db_session: Session, api_client: TestClient) -> None:
        db_session.add(_appointment_type())
        db_session.add(_rule())
        db_session.flush()

        response = api_client.post(
            "/api/v1/bookings", json=_payload(starts_at="2026-09-07T08:00:00")
        )

        assert response.status_code == 422

    def test_rejects_a_confirmed_booking_on_top_of_another(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        """Las reglas de disponibilidad son globales (sin appointment_type_id): un mismo
        hueco de calendario sirve para cualquier tipo de cita, así que reservarlo con un
        tipo distinto tiene que chocar igual -- es el pre-check, y no una coincidencia de
        payload, quien lo detecta."""
        db_session.add_all(
            [
                _appointment_type(),
                _appointment_type(slug="seguimiento", name="Seguimiento"),
            ]
        )
        db_session.add(_rule())
        db_session.flush()

        first = api_client.post("/api/v1/bookings", json=_payload())
        assert first.status_code == 201

        second = api_client.post("/api/v1/bookings", json=_payload(type="seguimiento"))

        assert second.status_code == 409
        assert second.json()["code"] == "slot_unavailable"


@pytest.mark.db
class TestGetBooking:
    def test_returns_the_booking_by_token(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()
        booking = _booking(appointment_type.id)
        db_session.add(booking)
        db_session.flush()

        response = api_client.get(f"/api/v1/bookings/{booking.token}")

        assert response.status_code == 200
        assert response.json() == {
            "token": booking.token,
            "reference": booking.reference,
            "status": "confirmed",
            "starts_at": "2026-09-07T08:00:00Z",
            "ends_at": "2026-09-07T08:30:00Z",
            "customer_name": "Ada Lovelace",
            "appointment_type": "reunion-inicial",
            "appointment_type_name": "Reunión inicial",
        }

    def test_returns_404_for_an_unknown_token(self, api_client: TestClient) -> None:
        response = api_client.get("/api/v1/bookings/no-existe-este-token")

        assert response.status_code == 404
        assert response.json() == {
            "code": "booking_not_found",
            "detail": "No existe ninguna reserva con ese token.",
        }


@pytest.mark.db
class TestCancelBooking:
    def test_cancels_a_confirmed_booking(self, db_session: Session, api_client: TestClient) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()
        booking = _booking(appointment_type.id)
        db_session.add(booking)
        db_session.flush()

        response = api_client.post(f"/api/v1/bookings/{booking.token}/cancel")

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cancelling_twice_is_idempotent(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.flush()
        booking = _booking(appointment_type.id)
        db_session.add(booking)
        db_session.flush()

        first = api_client.post(f"/api/v1/bookings/{booking.token}/cancel")
        second = api_client.post(f"/api/v1/bookings/{booking.token}/cancel")

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["status"] == second.json()["status"] == "cancelled"

    def test_cancelling_frees_the_slot_for_a_new_booking(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.add(_rule())
        db_session.flush()
        booking = _booking(appointment_type.id)
        db_session.add(booking)
        db_session.flush()

        # Antes de cancelar, el hueco está ocupado.
        blocked = api_client.post("/api/v1/bookings", json=_payload())
        assert blocked.status_code == 409

        cancel = api_client.post(f"/api/v1/bookings/{booking.token}/cancel")
        assert cancel.status_code == 200

        rebooked = api_client.post("/api/v1/bookings", json=_payload())
        assert rebooked.status_code == 201

    def test_returns_404_for_an_unknown_token(self, api_client: TestClient) -> None:
        response = api_client.post("/api/v1/bookings/no-existe-este-token/cancel")

        assert response.status_code == 404
        assert response.json()["code"] == "booking_not_found"


@pytest.mark.db
class TestRescheduleBooking:
    def test_moves_the_booking_to_a_new_free_slot(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.add(_rule())
        db_session.flush()
        booking = _booking(appointment_type.id)
        db_session.add(booking)
        db_session.flush()
        token = booking.token

        response = api_client.post(
            f"/api/v1/bookings/{token}/reschedule",
            json={"starts_at": _OTHER_FREE_SLOT_STARTS_AT},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["token"] == token
        assert body["starts_at"] == "2026-09-07T08:30:00Z"
        assert body["ends_at"] == "2026-09-07T09:00:00Z"

    def test_rescheduling_to_the_same_slot_does_not_conflict_with_itself(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.add(_rule())
        db_session.flush()
        booking = _booking(appointment_type.id)
        db_session.add(booking)
        db_session.flush()

        response = api_client.post(
            f"/api/v1/bookings/{booking.token}/reschedule",
            json={"starts_at": _FREE_SLOT_STARTS_AT},
        )

        assert response.status_code == 200

    def test_rescheduling_frees_the_old_slot_for_a_new_booking(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.add(_rule())
        db_session.flush()
        booking = _booking(appointment_type.id)
        db_session.add(booking)
        db_session.flush()

        reschedule = api_client.post(
            f"/api/v1/bookings/{booking.token}/reschedule",
            json={"starts_at": _OTHER_FREE_SLOT_STARTS_AT},
        )
        assert reschedule.status_code == 200

        rebooked = api_client.post("/api/v1/bookings", json=_payload())
        assert rebooked.status_code == 201

    def test_rejects_a_slot_already_taken_by_another_booking(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.add(_rule())
        db_session.flush()
        booking = _booking(appointment_type.id)
        other = _booking(
            appointment_type.id,
            starts_at=datetime(2026, 9, 7, 8, 30, tzinfo=UTC),
            ends_at=datetime(2026, 9, 7, 9, 0, tzinfo=UTC),
        )
        db_session.add_all([booking, other])
        db_session.flush()

        response = api_client.post(
            f"/api/v1/bookings/{booking.token}/reschedule",
            json={"starts_at": _OTHER_FREE_SLOT_STARTS_AT},
        )

        assert response.status_code == 409
        assert response.json()["code"] == "slot_unavailable"

    def test_returns_404_for_an_unknown_token(self, api_client: TestClient) -> None:
        response = api_client.post(
            "/api/v1/bookings/no-existe-este-token/reschedule",
            json={"starts_at": _FREE_SLOT_STARTS_AT},
        )

        assert response.status_code == 404
        assert response.json()["code"] == "booking_not_found"
