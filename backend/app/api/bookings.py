"""Ruta pública de creación de reservas: POST /api/v1/bookings.

Sin autenticación, como el resto de app/api/availability.py. Tres pasos, cada uno en su
propia función: buscar el tipo de cita, comprobar que el hueco sigue libre y crear la
reserva -- así un cambio futuro (el email de confirmación de FEAT 16, por ejemplo) se
añade como un cuarto paso en create_booking sin tocar los otros tres.
"""

from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.availability import fetch_free_slots
from app.core.db import get_db
from app.core.errors import ApiError
from app.core.timezone import booking_timezone, utc_now, utc_to_local_date
from app.models import AppointmentType, Booking
from app.schemas.booking import BookingCreate, BookingOut

router = APIRouter(prefix="/api/v1")


def _slot_unavailable() -> ApiError:
    return ApiError(409, "slot_unavailable", "Ese horario ya no está disponible.")


def _find_active_appointment_type(db: Session, slug: str) -> AppointmentType:
    appointment_type = db.scalars(
        select(AppointmentType).where(
            AppointmentType.slug == slug,
            AppointmentType.is_active.is_(True),
        )
    ).one_or_none()
    if appointment_type is None:
        raise ApiError(404, "appointment_type_not_found", "No existe ese tipo de cita.")
    return appointment_type


def _ensure_slot_is_free(
    db: Session, appointment_type: AppointmentType, starts_at: datetime
) -> None:
    """Solo UX: reutiliza fetch_free_slots, la misma consulta que GET /availability, así
    que nunca puede ofrecer un hueco distinto del que luego rechaza aquí. La garantía real
    es el EXCLUDE de BD (5.5) -- ver _insert_booking."""
    tz = booking_timezone()
    local_day = utc_to_local_date(starts_at, tz)
    slots = fetch_free_slots(db, appointment_type, local_day, local_day, tz, utc_now())
    if not any(slot.starts_at == starts_at for slot in slots):
        raise _slot_unavailable()


def _insert_booking(
    db: Session, appointment_type: AppointmentType, booking_in: BookingCreate
) -> Booking:
    """Lo que de verdad decide, no el pre-check de arriba: dos peticiones casi
    simultáneas sobre el mismo hueco pasan igual _ensure_slot_is_free, y solo una gana el
    EXCLUDE de app/models/booking.py al hacer commit (probado con concurrencia real en
    tests/test_booking_concurrency.py)."""
    booking = Booking(
        appointment_type_id=appointment_type.id,
        customer_name=booking_in.customer_name,
        customer_email=booking_in.customer_email,
        starts_at=booking_in.starts_at,
        ends_at=booking_in.starts_at + timedelta(minutes=appointment_type.duration_minutes),
    )
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _slot_unavailable() from None
    db.refresh(booking)
    return booking

#Endpoint público de creación de reservas: POST /api/v1/bookings, sin autenticación.
@router.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(
    booking_in: BookingCreate,
    db: Annotated[Session, Depends(get_db)],
    response: Response,
) -> Booking:
    appointment_type = _find_active_appointment_type(db, booking_in.appointment_type)
    _ensure_slot_is_free(db, appointment_type, booking_in.starts_at)
    booking = _insert_booking(db, appointment_type, booking_in)

    response.headers["Location"] = f"/api/v1/bookings/{booking.token}"
    return booking
