"""Tests de los endpoints públicos de disponibilidad, contra Postgres de verdad.

Usan api_client (tests/conftest.py), no client: el endpoint necesita ver dentro de la
misma transacción las filas que cada test prepara con db_session.
"""

from datetime import date, datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.availability import AVAILABILITY_CACHE_CONTROL
from app.core.timezone import local_to_utc
from app.models import AppointmentType, AvailabilityRule, Booking


def _next_monday() -> date:
    """Un lunes futuro y no una fecha fija: compute_free_slots descarta todo hueco
    anterior a `now` (app/services/availability.py), así que una fecha fija se habría
    ido quedando atrás según pasan los días -- que es justo lo que le pasó a esta
    suite."""
    today = date.today()
    days_ahead = (7 - today.weekday()) % 7 or 7
    return today + timedelta(days=days_ahead)


def _as_iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


_SLOT_DATE = _next_monday()
_NEXT_DAY = _SLOT_DATE + timedelta(days=1)
# Primer slot libre de _rule(): las 10:00 de Madrid, con el desfase que esté vigente ese
# día (CET o CEST según la época del año).
_FREE_SLOT_START = local_to_utc(_SLOT_DATE, time(10, 0))


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
        "weekday": _SLOT_DATE.weekday(),  # lunes
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
        db_session.add(_rule())  # solo cubre _SLOT_DATE (lunes)
        db_session.flush()

        response = api_client.get(
            "/api/v1/availability",
            params={
                "type": "reunion-inicial",
                "from": _SLOT_DATE.isoformat(),
                "to": _NEXT_DAY.isoformat(),
            },
        )

        assert response.status_code == 200
        days = response.json()
        assert [day["date"] for day in days] == [_SLOT_DATE.isoformat(), _NEXT_DAY.isoformat()]

        monday, tuesday = days
        assert len(monday["slots"]) == 8  # 10:00-14:00 Madrid, treinta minutos cada slot
        assert monday["slots"][0]["starts_at"] == _as_iso(_FREE_SLOT_START)
        # El día siguiente no tiene regla -> día presente, con la lista vacía, no ausente.
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
                starts_at=_FREE_SLOT_START,
                ends_at=_FREE_SLOT_START + timedelta(minutes=30),
            )
        )
        db_session.flush()

        response = api_client.get(
            "/api/v1/availability",
            params={
                "type": "reunion-inicial",
                "from": _SLOT_DATE.isoformat(),
                "to": _SLOT_DATE.isoformat(),
            },
        )

        assert response.status_code == 200
        slots = response.json()[0]["slots"]
        assert len(slots) == 7  # libres tras la reserva, treinta minutos cada slot
        assert slots[0]["starts_at"] == _as_iso(_FREE_SLOT_START + timedelta(minutes=30))

    def test_a_cancelled_booking_frees_its_slot_again(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        """Fija el filtro por estado del predicado de solape: el `&&` selecciona la fila
        igual, y lo que la descarta es `status == 'confirmed'`."""
        appointment_type = _appointment_type(buffer_minutes=0)
        db_session.add(appointment_type)
        db_session.add(_rule())
        db_session.flush()

        db_session.add(
            Booking(
                appointment_type_id=appointment_type.id,
                customer_name="Ada Lovelace",
                customer_email="ada@example.com",
                starts_at=_FREE_SLOT_START,
                ends_at=_FREE_SLOT_START + timedelta(minutes=30),
                status="cancelled",
            )
        )
        db_session.flush()

        response = api_client.get(
            "/api/v1/availability",
            params={
                "type": "reunion-inicial",
                "from": _SLOT_DATE.isoformat(),
                "to": _SLOT_DATE.isoformat(),
            },
        )

        assert response.status_code == 200
        slots = response.json()[0]["slots"]
        assert len(slots) == 8
        assert slots[0]["starts_at"] == _as_iso(_FREE_SLOT_START)

    def test_a_booking_that_only_touches_the_window_edge_does_not_block_it(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        """El rango es semiabierto `[)`: una reserva que termina justo cuando empieza el día
        pedido no se solapa con él y no puede quitarle ningún hueco."""
        appointment_type = _appointment_type(buffer_minutes=0)
        db_session.add(appointment_type)
        db_session.add(_rule())
        db_session.flush()

        # Medianoche local de _SLOT_DATE es justo el borde inferior de la ventana que
        # consulta el endpoint (local_day_bounds, app/core/timezone.py).
        day_start = local_to_utc(_SLOT_DATE, time.min)
        db_session.add(
            Booking(
                appointment_type_id=appointment_type.id,
                customer_name="Ada Lovelace",
                customer_email="ada@example.com",
                starts_at=day_start - timedelta(minutes=30),
                ends_at=day_start,
            )
        )
        db_session.flush()

        response = api_client.get(
            "/api/v1/availability",
            params={
                "type": "reunion-inicial",
                "from": _SLOT_DATE.isoformat(),
                "to": _SLOT_DATE.isoformat(),
            },
        )

        assert response.status_code == 200
        assert len(response.json()[0]["slots"]) == 8

    def test_the_response_is_cacheable_for_a_minute(
        self, db_session: Session, api_client: TestClient
    ) -> None:
        db_session.add(_appointment_type())
        db_session.flush()

        response = api_client.get(
            "/api/v1/availability",
            params={"type": "reunion-inicial", "from": "2026-09-07", "to": "2026-09-07"},
        )

        assert response.headers["cache-control"] == AVAILABILITY_CACHE_CONTROL

    def test_a_404_is_not_cached(self, api_client: TestClient) -> None:
        """El Cache-Control se pone solo en el camino bueno: cachear un 404 dejaría un tipo
        de cita recién activado invisible durante un minuto."""
        response = api_client.get(
            "/api/v1/availability",
            params={"type": "no-existe", "from": "2026-09-07", "to": "2026-09-07"},
        )

        assert response.status_code == 404
        assert "cache-control" not in response.headers
