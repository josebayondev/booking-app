"""Tests de los endpoints públicos de disponibilidad, contra Postgres de verdad.

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
        "buffer_minutes": 15,
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


@pytest.mark.db
class TestAppointmentTypes:
    def test_lists_only_active_types_ordered_by_sort_order(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        db_session.add_all(
            [
                _appointment_type(slug="segunda", name="Segunda", sort_order=1),
                _appointment_type(slug="primera", name="Primera", sort_order=0),
                _appointment_type(slug="inactiva", name="Inactiva", is_active=False),
            ]
        )
        db_session.flush()

        response = api_client.get("/api/v1/appointment-types")

        assert response.status_code == 200
        assert [item["slug"] for item in response.json()] == ["primera", "segunda"]


@pytest.mark.db
class TestAvailability:
    def test_returns_404_for_an_unknown_slug(self, api_client: TestClient) -> None:
        response = api_client.get(
            "/api/v1/availability",
            params={"type": "no-existe", "from": "2026-09-07", "to": "2026-09-07"},
        )

        assert response.status_code == 404
        assert response.json() == {
            "code": "appointment_type_not_found",
            "detail": "No existe ese tipo de cita.",
        }

    def test_returns_404_for_an_inactive_type(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        db_session.add(_appointment_type(is_active=False))
        db_session.flush()

        response = api_client.get(
            "/api/v1/availability",
            params={"type": "reunion-inicial", "from": "2026-09-07", "to": "2026-09-07"},
        )

        assert response.status_code == 404
        assert response.json()["code"] == "appointment_type_not_found"

    def test_rejects_a_reversed_date_range(self, client: TestClient) -> None:
        """No necesita base de datos: la validación ocurre antes de llegar al router."""
        response = client.get(
            "/api/v1/availability",
            params={"type": "reunion-inicial", "from": "2026-09-10", "to": "2026-09-01"},
        )

        assert response.status_code == 422

    def test_rejects_a_range_longer_than_62_days(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/availability",
            params={"type": "reunion-inicial", "from": "2026-09-07", "to": "2026-12-07"},
        )

        assert response.status_code == 422

    def test_returns_every_requested_day_grouped_with_its_own_slots(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type()
        db_session.add(appointment_type)
        db_session.add(_rule())  # solo cubre el lunes 2026-09-07
        db_session.flush()

        response = api_client.get(
            "/api/v1/availability",
            params={"type": "reunion-inicial", "from": "2026-09-07", "to": "2026-09-08"},
        )

        assert response.status_code == 200
        days = response.json()
        assert [day["date"] for day in days] == ["2026-09-07", "2026-09-08"]

        monday, tuesday = days
        assert len(monday["slots"]) == 8  # 10:00-14:00 Madrid, treinta minutos cada slot
        # 10:00 en Madrid es verano (CEST, UTC+2) -> 08:00Z.
        assert monday["slots"][0]["starts_at"] == "2026-09-07T08:00:00Z"
        # Martes no tiene regla -> día presente, con la lista vacía, no ausente.
        assert tuesday["slots"] == []

    def test_excludes_a_confirmed_booking(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        appointment_type = _appointment_type(buffer_minutes=0)
        db_session.add(appointment_type)
        db_session.add(_rule())
        db_session.flush()

        db_session.add(
            Booking(
                appointment_type_id=appointment_type.id,
                customer_name="Ada Lovelace",
                customer_email="ada@example.com",
                starts_at=datetime(2026, 9, 7, 8, 0, tzinfo=UTC),
                ends_at=datetime(2026, 9, 7, 8, 30, tzinfo=UTC),
            )
        )
        db_session.flush()

        response = api_client.get(
            "/api/v1/availability",
            params={"type": "reunion-inicial", "from": "2026-09-07", "to": "2026-09-07"},
        )

        assert response.status_code == 200
        slots = response.json()[0]["slots"]
        assert len(slots) == 7  # 08:30-12:00Z libres tras la reserva, treinta minutos cada slot
        assert slots[0]["starts_at"] == "2026-09-07T08:30:00Z"
