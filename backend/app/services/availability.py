"""Cálculo de huecos reservables: la función que convierte cuatro tablas de
configuración en "esto es lo que puedes reservar".

Es la lógica más delicada de todo el proyecto -- combina la asimetría de zonas horarias
(app/core/timezone.py), buffers, ventanas de antelación y solapes -- así que vive aquí,
separada de cualquier acceso a base de datos, para poder probarse con datos inventados a
mano sin tocar Postgres ni depender de la hora real de ejecución.
"""

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import NamedTuple
from zoneinfo import ZoneInfo

from app.core.timezone import booking_timezone, local_day_bounds, local_to_utc, utc_to_local_date
from app.models import AppointmentType, AvailabilityException, AvailabilityRule

Interval = tuple[datetime, datetime]


class BookingWithBuffer(NamedTuple):
    """Lo mínimo que hace falta de una reserva ya existente para bloquear un hueco.

    buffer_minutes es el de SU PROPIO tipo de cita, nunca el del tipo que se está
    consultando ahora: el calendario es único y compartido entre todos los tipos, así
    que una reserva de un tipo con un buffer distinto bloquea igual, con su propio
    colchón. Quien llama a compute_free_slots la construye uniendo Booking con su
    AppointmentType.
    """

    starts_at: datetime
    ends_at: datetime
    status: str
    buffer_minutes: int


class FreeSlot(NamedTuple):
    starts_at: datetime
    ends_at: datetime


def _merge(intervals: list[Interval]) -> list[Interval]:
    """Funde intervalos solapados o contiguos en el mínimo conjunto disjunto.

    Imprescindible antes de trocear: el modelo permite a propósito dos AvailabilityRule
    solapadas el mismo día (ver el comentario del UniqueConstraint en
    app/models/availability.py, "producen la unión de los huecos"), y trocear cada una
    por separado antes de fundirlas generaría slots duplicados en la franja común.
    """
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda interval: interval[0])
    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _subtract(intervals: list[Interval], blockers: list[Interval]) -> list[Interval]:
    """Resta cada bloqueante de la lista de intervalos libres.

    Un bloqueante puede encoger un intervalo por un lado, partirlo en dos, o hacerlo
    desaparecer entero si lo cubre por completo. blockers no necesita venir fundido:
    cada uno se aplica por turnos sobre el resultado del anterior.
    """
    for block_start, block_end in blockers:
        next_intervals: list[Interval] = []
        for start, end in intervals:
            if block_end <= start or block_start >= end:
                next_intervals.append((start, end))
                continue
            if block_start > start:
                next_intervals.append((start, block_start))
            if block_end < end:
                next_intervals.append((block_end, end))
        intervals = next_intervals
    return intervals


def compute_free_slots(
    *,
    appointment_type: AppointmentType,
    rules: Sequence[AvailabilityRule],
    exceptions: Sequence[AvailabilityException],
    bookings: Sequence[BookingWithBuffer],
    window_start: date,
    window_end: date,
    now: datetime,
    tz: ZoneInfo | None = None,
) -> list[FreeSlot]:
    """Los huecos reservables de appointment_type entre window_start y window_end
    (fechas locales, ambas inclusive).

    Precondiciones que esta función no puede comprobar por sí misma -- son
    responsabilidad de quien la llama:

    - exceptions y bookings deben cubrir, como mínimo,
      [local_day_bounds(window_start, tz)[0], local_day_bounds(window_end, tz)[1]).
      Nunca compares un date directamente contra una columna TIMESTAMPTZ: el desfase
      horario perdería o incluiría filas de más cerca de los bordes.
    - appointment_type.is_active se comprueba antes de llamar (404 en el router si no
      lo está) -- esta función no lo mira.

    El orden de las operaciones evita dos bugs concretos, no es un orden arbitrario:

    1. Se funden reglas + aperturas extra en un único conjunto disjunto ANTES de
       trocear en bloques de duration_minutes. Trocear por regla y fundir después
       duplicaría slots en la franja donde dos reglas se solapan.
    2. El troceo ancla cada bloque al inicio del intervalo libre ya fundido, y el
       filtro de antelación (earliest/latest) se aplica DESPUÉS, descartando el bloque
       entero en vez de recortarlo. Recortar antes de trocear desplazaría el ancla de
       la rejilla al instante exacto en que expira la antelación mínima, en vez de al
       horario real de la regla.
    """
    tz = tz or booking_timezone()

    if window_start > window_end:
        raise ValueError("el rango de fechas es inválido: window_start es posterior a window_end")

    earliest = now + timedelta(hours=appointment_type.min_notice_hours)
    latest_local_date = utc_to_local_date(now, tz) + timedelta(
        days=appointment_type.max_advance_days
    )
    _, latest = local_day_bounds(latest_local_date, tz)

    free: list[Interval] = []
    extra_open: list[Interval] = []
    blocked: list[Interval] = []

    day = window_start
    while day <= window_end:
        weekday = day.weekday()
        for rule in rules:
            if rule.weekday == weekday and rule.is_active:
                free.append(
                    (
                        local_to_utc(day, rule.starts_at_local, tz),
                        local_to_utc(day, rule.ends_at_local, tz),
                    )
                )
        day += timedelta(days=1)

    for exception in exceptions:
        target = extra_open if exception.is_available else blocked
        target.append((exception.starts_at, exception.ends_at))

    free = _merge(free + extra_open)

    booking_blocks = [
        (
            booking.starts_at - timedelta(minutes=booking.buffer_minutes),
            booking.ends_at + timedelta(minutes=booking.buffer_minutes),
        )
        for booking in bookings
        if booking.status == "confirmed"
    ]

    free = _subtract(free, blocked)
    free = _subtract(free, booking_blocks)

    duration = timedelta(minutes=appointment_type.duration_minutes)
    slots: list[FreeSlot] = []
    for start, end in free:
        current = start
        while current + duration <= end:
            slot_end = current + duration
            if current >= earliest and slot_end <= latest:
                slots.append(FreeSlot(current, slot_end))
            current = slot_end

    slots.sort(key=lambda slot: slot.starts_at)
    return slots
