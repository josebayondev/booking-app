"""Ruta pública de creación de reservas: POST /api/v1/bookings.

Sin autenticación, como el resto de app/api/availability.py.
"""

from datetime import timedelta
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


# Endpoint público de creación de reservas, sin autenticación. La única forma de llegar
# a una reserva ya creada es con su token secreto, que se devuelve en la respuesta y se
# envía por email al cliente. El token es un secreto de 32 bytes codificado en base64
# urlsafe.
@router.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(
    booking_in: BookingCreate,
    db: Annotated[Session, Depends(get_db)],
    response: Response,
) -> Booking:
    # 1. El tipo de cita tiene que existir y estar activo.
    appointment_type = db.scalars(
        select(AppointmentType).where(
            AppointmentType.slug == booking_in.appointment_type,
            AppointmentType.is_active.is_(True),
        )
    ).one_or_none()
    if appointment_type is None:
        raise ApiError(404, "appointment_type_not_found", "No existe ese tipo de cita.")

    # 2. Pre-check de UX: reutiliza la misma consulta que GET /availability
    # (fetch_free_slots, en app/api/availability.py), así que nunca puede ofrecer un
    # hueco distinto del que luego rechaza aquí. La garantía real es el EXCLUDE de BD
    # (5.5) -- paso 3.
    tz = booking_timezone()
    local_day = utc_to_local_date(booking_in.starts_at, tz)
    slots = fetch_free_slots(db, appointment_type, local_day, local_day, tz, utc_now())
    if not any(slot.starts_at == booking_in.starts_at for slot in slots):
        raise ApiError(409, "slot_unavailable", "Ese horario ya no está disponible.")

    # 3. Lo que de verdad decide, no el pre-check de arriba: dos peticiones casi
    # simultáneas sobre el mismo hueco pasan igual el paso 2, y solo una gana el EXCLUDE
    # de app/models/booking.py al hacer commit (probado con concurrencia real en
    # tests/test_booking_concurrency.py).
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
        raise ApiError(409, "slot_unavailable", "Ese horario ya no está disponible.") from None
    db.refresh(booking)

    response.headers["Location"] = f"/api/v1/bookings/{booking.token}"
    return booking
