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
from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import ColumnElement, ColumnExpressionArgument, func, literal_column, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import ApiError
from app.core.timezone import booking_timezone, local_day_bounds, utc_now, utc_to_local_date
from app.models import AppointmentType, AvailabilityException, AvailabilityRule, Booking
from app.schemas.appointment_type import AppointmentTypeOut
from app.schemas.availability import AvailabilityQuery, DayAvailabilityOut, FreeSlotOut
from app.services.availability import BookingWithBuffer, compute_free_slots

router = APIRouter(prefix="/api/v1")

# Cuánto puede quedarse cacheada una respuesta de disponibilidad. Un minuto de desfase
# significa que un hueco recién ocupado puede seguir ofreciéndose durante ese minuto; la
# reserva fallaría entonces contra el EXCLUDE de la base de datos, que es justo la garantía
# que hace seguro este desfase. A cambio, el calendario del frontend deja de repreguntar
# por cada repintado, que es de donde viene casi todo el tráfico legítimo.
AVAILABILITY_CACHE_CONTROL = "public, max-age=60"

# El literal '[)' va como literal_column y no como parámetro ligado a propósito. El índice
# GiST que crea el ExcludeConstraint de Booking está construido sobre la expresión
# `tstzrange(starts_at, ends_at, '[)')` con ese literal dentro, y Postgres empareja un
# índice de expresión comparando árboles: un parámetro ligado no es el mismo nodo que una
# constante, así que emitirlo como bind podría dejar el índice sin usar.
_RANGE_BOUNDS: ColumnElement[str] = literal_column("'[)'")


def _overlaps(
    start_column: ColumnExpressionArgument[datetime],
    end_column: ColumnExpressionArgument[datetime],
    window_start: datetime,
    window_end: datetime,
) -> ColumnElement[bool]:
    """Filas cuyo [start, end) se solapa con [window_start, window_end).

    Escrito con el operador de rangos `&&` y no como dos comparaciones sueltas
    (`start < fin AND end > inicio`) porque el `&&` es lo que un índice GiST sabe servir.
    Las dos comparaciones obligan al planner a tirar del índice b-tree de starts_at, cuyo
    predicado `starts_at < window_end` -- con window_end en el futuro -- selecciona el
    histórico entero y deja la mitad selectiva como filtro posterior. Da igual con la tabla
    vacía y se degrada linealmente con los años.
    """
    return func.tstzrange(start_column, end_column, _RANGE_BOUNDS).bool_op("&&")(
        func.tstzrange(window_start, window_end, _RANGE_BOUNDS)
    )


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
    response: Response,
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
                _overlaps(
                    AvailabilityException.starts_at,
                    AvailabilityException.ends_at,
                    fetch_start,
                    fetch_end,
                )
            )
        ).all()

        booking_rows = db.execute(
            select(
                Booking.starts_at, Booking.ends_at, Booking.status, AppointmentType.buffer_minutes
            )
            .join(AppointmentType, Booking.appointment_type_id == AppointmentType.id)
            .where(
                # El índice GiST es parcial sobre `status <> 'cancelled'`; Postgres deduce
                # que `= 'confirmed'` lo implica y lo usa igual. Se filtra por el valor
                # exacto y no por `<> 'cancelled'` porque es lo que significa de verdad
                # "esta reserva ocupa el hueco", y seguiría siendo correcto si algún día
                # apareciese un tercer estado.
                Booking.status == "confirmed",
                _overlaps(Booking.starts_at, Booking.ends_at, fetch_start, fetch_end),
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

    # Solo en el camino bueno: el 404 de más arriba sale del exception_handler de ApiError,
    # que construye su propia respuesta y no pasa por este objeto.
    response.headers["Cache-Control"] = AVAILABILITY_CACHE_CONTROL

    return days
