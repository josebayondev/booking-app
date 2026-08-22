"""Rutas públicas de disponibilidad: qué tipos de cita existen y qué huecos hay libres.

Sin autenticación -- la reserva pública no tiene login. Todo lo que toca la base de
datos vive aquí; compute_free_slots (app/services/availability.py) se queda ciego a
Postgres a propósito, así que aquí es donde se cumple su precondición de fetch: los
límites de la consulta salen de local_day_bounds(), nunca de comparar un date
directamente contra una columna TIMESTAMPTZ.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.timezone import booking_timezone, local_day_bounds, utc_now, utc_to_local_date
from app.models import AppointmentType, AvailabilityException, AvailabilityRule, Booking
from app.schemas.appointment_type import AppointmentTypeOut
from app.schemas.availability import AvailabilityQuery, FreeSlotOut
from app.services.availability import BookingWithBuffer, compute_free_slots

router = APIRouter()


@router.get("/appointment-types", response_model=list[AppointmentTypeOut])
def list_appointment_types(db: Annotated[Session, Depends(get_db)]) -> list[AppointmentType]:
    stmt = (
        select(AppointmentType)
        .where(AppointmentType.is_active.is_(True))
        .order_by(AppointmentType.sort_order)
    )
    return list(db.scalars(stmt))


@router.get("/availability", response_model=list[FreeSlotOut])
def get_availability(
    query: Annotated[AvailabilityQuery, Query()],
    db: Annotated[Session, Depends(get_db)],
) -> list[FreeSlotOut]:
    appointment_type = db.scalars(
        select(AppointmentType).where(
            AppointmentType.slug == query.appointment_type,
            AppointmentType.is_active.is_(True),
        )
    ).one_or_none()
    if appointment_type is None:
        raise HTTPException(status_code=404, detail="Appointment type not found")

    tz = booking_timezone()
    now = utc_now()

    # Nunca dejar que un rango absurdo (años) fuerce un bucle diario enorme en
    # compute_free_slots por pura entrada de query param: se acota "to" a lo que la
    # propia política del tipo de cita permite reservar como muy tarde.
    latest_bookable_date = utc_to_local_date(now, tz) + timedelta(
        days=appointment_type.max_advance_days
    )
    window_end = min(query.date_to, latest_bookable_date)
    if window_end < query.date_from:
        return []

    fetch_start, _ = local_day_bounds(query.date_from, tz)
    _, fetch_end = local_day_bounds(window_end, tz)

    rules = db.scalars(select(AvailabilityRule).where(AvailabilityRule.is_active.is_(True))).all()

    exceptions = db.scalars(
        select(AvailabilityException).where(
            AvailabilityException.starts_at < fetch_end,
            AvailabilityException.ends_at > fetch_start,
        )
    ).all()

    booking_rows = db.execute(
        select(Booking.starts_at, Booking.ends_at, Booking.status, AppointmentType.buffer_minutes)
        .join(AppointmentType, Booking.appointment_type_id == AppointmentType.id)
        .where(
            Booking.status == "confirmed",
            Booking.starts_at < fetch_end,
            Booking.ends_at > fetch_start,
        )
    ).all()
    bookings = [
        BookingWithBuffer(
            starts_at=starts_at, ends_at=ends_at, status=status, buffer_minutes=buffer_minutes
        )
        for starts_at, ends_at, status, buffer_minutes in booking_rows
    ]

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=rules,
        exceptions=exceptions,
        bookings=bookings,
        window_start=query.date_from,
        window_end=window_end,
        now=now,
        tz=tz,
    )
    return [FreeSlotOut(starts_at=slot.starts_at, ends_at=slot.ends_at) for slot in slots]
