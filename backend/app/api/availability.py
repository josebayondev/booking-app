"""Rutas públicas de disponibilidad: qué tipos de cita existen y qué huecos hay libres.

Sin autenticación -- la reserva pública no tiene login. Todo lo que toca la base de
datos vive aquí; compute_free_slots (app/services/availability.py) se queda ciego a
Postgres a propósito, así que aquí es donde se cumple su precondición de fetch: los
límites de la consulta salen de local_day_bounds(), nunca de comparar un date
directamente contra una columna TIMESTAMPTZ.

Bajo /api/v1 desde el primer día (FEAT 13): cambiar el prefijo más adelante, con clientes
de verdad enganchados (frontend, y el chatbot de FEAT 17), costaría mucho más que fijarlo
ahora que solo hay dos rutas.
"""

from collections import defaultdict
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.core.timezone import booking_timezone, local_day_bounds, utc_now, utc_to_local_date
from app.models import AppointmentType, AvailabilityException, AvailabilityRule, Booking
from app.schemas.appointment_type import AppointmentTypeOut
from app.schemas.availability import AvailabilityQuery, DayAvailabilityOut, FreeSlotOut
from app.services.availability import BookingWithBuffer, compute_free_slots

router = APIRouter(prefix="/api/v1")


@router.get("/appointment-types", response_model=list[AppointmentTypeOut])
def list_appointment_types(db: Annotated[Session, Depends(get_db)]) -> list[AppointmentType]:
    stmt = (
        select(AppointmentType)
        .where(AppointmentType.is_active.is_(True))
        .order_by(AppointmentType.sort_order)
    )
    return list(db.scalars(stmt))


@router.get("/availability", response_model=list[DayAvailabilityOut])
def get_availability(
    query: Annotated[AvailabilityQuery, Query()],
    db: Annotated[Session, Depends(get_db)],
) -> list[DayAvailabilityOut]:
    appointment_type = db.scalars(
        select(AppointmentType).where(
            AppointmentType.slug == query.appointment_type,
            AppointmentType.is_active.is_(True),
        )
    ).one_or_none()
    if appointment_type is None:
        raise ApiError(404, "appointment_type_not_found", "No existe ese tipo de cita.")

    tz = booking_timezone()
    now = utc_now()

    # Nunca dejar que un rango que el policy no permite reservar fuerce un bucle diario
    # inútil en compute_free_slots -- el propio schema ya rechaza más de 62 días, pero
    # max_advance_days puede ser más corto todavía.
    latest_bookable_date = utc_to_local_date(now, tz) + timedelta(
        days=appointment_type.max_advance_days
    )
    window_end = min(query.date_to, latest_bookable_date)

    slots_by_day: dict[date, list[FreeSlotOut]] = defaultdict(list)

    if window_end >= query.date_from:
        fetch_start, _ = local_day_bounds(query.date_from, tz)
        _, fetch_end = local_day_bounds(window_end, tz)

        rules = db.scalars(
            select(AvailabilityRule).where(AvailabilityRule.is_active.is_(True))
        ).all()

        exceptions = db.scalars(
            select(AvailabilityException).where(
                AvailabilityException.starts_at < fetch_end,
                AvailabilityException.ends_at > fetch_start,
            )
        ).all()

        booking_rows = db.execute(
            select(
                Booking.starts_at, Booking.ends_at, Booking.status, AppointmentType.buffer_minutes
            )
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
        for slot in slots:
            slot_day = utc_to_local_date(slot.starts_at, tz)
            slots_by_day[slot_day].append(
                FreeSlotOut(starts_at=slot.starts_at, ends_at=slot.ends_at)
            )

    # Un DayAvailabilityOut por cada día pedido, incluso sin huecos -- para que el
    # frontend pinte el mes de un tirón sin tener que rellenar los días que faltan.
    days: list[DayAvailabilityOut] = []
    day = query.date_from
    while day <= query.date_to:
        days.append(DayAvailabilityOut(date=day, slots=slots_by_day.get(day, [])))
        day += timedelta(days=1)

    return days
