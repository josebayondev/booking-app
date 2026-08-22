"""Tests puros de compute_free_slots: sin Postgres, sin reloj real -- todo lo que hace
falta se inventa a mano y se inyecta por parámetro.

Cada test fija uno de los casos límite que motivaron el diseño (ver el docstring de
app/services/availability.py): fusionar antes de trocear, filtrar en vez de recortar por
antelación, y el buffer que viaja con cada reserva y no con el tipo consultado.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.timezone import local_to_utc
from app.models import AppointmentType, AvailabilityException, AvailabilityRule
from app.services.availability import BookingWithBuffer, compute_free_slots

MADRID = ZoneInfo("Europe/Madrid")

MONDAY = date(2026, 9, 7)
SATURDAY = date(2026, 9, 5)
# Los mismos domingos de cambio de hora que ya fija tests/test_timezone.py.
SPRING_FORWARD = date(2026, 3, 29)  # 02:00 CET -> 03:00 CEST, las 02:00-02:59 no existen
FALL_BACK = date(2026, 10, 25)  # 03:00 CEST -> 02:00 CET, las 02:00-02:59 pasan dos veces


def _appointment_type(**overrides: object) -> AppointmentType:
    defaults: dict[str, object] = {
        "slug": "reunion-inicial",
        "name": "Reunión inicial",
        "duration_minutes": 30,
        # No lo lee compute_free_slots: el buffer que aplica es el de cada
        # BookingWithBuffer, nunca el del tipo que se está consultando.
        "buffer_minutes": 15,
        "min_notice_hours": 0,
        "max_advance_days": 365,
    }
    return AppointmentType(**(defaults | overrides))


def _rule(**overrides: object) -> AvailabilityRule:
    defaults: dict[str, object] = {
        "weekday": MONDAY.weekday(),
        "starts_at_local": time(10, 0),
        "ends_at_local": time(14, 0),
        "is_active": True,
    }
    return AvailabilityRule(**(defaults | overrides))


def _exception(**overrides: object) -> AvailabilityException:
    defaults: dict[str, object] = {
        "starts_at": local_to_utc(MONDAY, time(9, 0), MADRID),
        "ends_at": local_to_utc(MONDAY, time(10, 0), MADRID),
        "is_available": False,
    }
    return AvailabilityException(**(defaults | overrides))


def _booking(
    start: datetime, end: datetime, buffer_minutes: int = 0, status: str = "confirmed"
) -> BookingWithBuffer:
    return BookingWithBuffer(
        starts_at=start, ends_at=end, status=status, buffer_minutes=buffer_minutes
    )


def _well_before(day: date) -> datetime:
    """Un "ahora" siete días antes de `day`, para los tests que no quieren que
    min_notice_hours ni max_advance_days entren en juego por accidente."""
    return local_to_utc(day - timedelta(days=7), time(0, 0), MADRID)


def test_notice_window_filters_whole_blocks_anchored_to_the_rule_not_to_now() -> None:
    """Fija la corrección más importante del diseño: recortar por antelación *antes* de
    trocear reancla la rejilla al instante exacto en que expira min_notice_hours, en vez
    de al horario real de la regla. Aquí `earliest` cae a mitad de un bloque (11:15, ni
    al principio ni al final de ningún slot de 30 min) para que la diferencia sea
    observable."""
    appointment_type = _appointment_type(min_notice_hours=0)
    rule = _rule()
    now = local_to_utc(MONDAY, time(11, 15), MADRID)

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=now,
        tz=MADRID,
    )

    starts = [slot.starts_at for slot in slots]
    # 11:00-11:30 empieza antes de las 11:15 -> se descarta entero, no se recorta a
    # 11:15-11:45. El primero que sobrevive sigue en la rejilla original de la regla.
    assert local_to_utc(MONDAY, time(11, 30), MADRID) in starts
    assert local_to_utc(MONDAY, time(11, 15), MADRID) not in starts
    assert local_to_utc(MONDAY, time(11, 0), MADRID) not in starts


def test_overlapping_rules_the_same_day_merge_without_duplicating_slots() -> None:
    """El modelo permite a propósito dos AvailabilityRule solapadas el mismo día (ver el
    UniqueConstraint en app/models/availability.py). Trocear cada una por separado antes
    de fundir duplicaría slots en la franja común."""
    appointment_type = _appointment_type()
    morning = _rule(starts_at_local=time(10, 0), ends_at_local=time(14, 0))
    afternoon = _rule(starts_at_local=time(12, 0), ends_at_local=time(16, 0))

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[morning, afternoon],
        exceptions=[],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    starts = [slot.starts_at for slot in slots]
    assert len(starts) == len(set(starts))
    assert len(slots) == 12  # 10:00-16:00, seis horas / 30 min
    assert local_to_utc(MONDAY, time(12, 0), MADRID) in starts


def test_two_separate_rules_the_same_day_do_not_create_phantom_slots() -> None:
    appointment_type = _appointment_type()
    morning = _rule(starts_at_local=time(9, 0), ends_at_local=time(13, 0))
    afternoon = _rule(starts_at_local=time(15, 0), ends_at_local=time(19, 0))

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[morning, afternoon],
        exceptions=[],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    assert len(slots) == 16  # cuatro horas + cuatro horas, treinta minutos cada slot
    lunch_start = local_to_utc(MONDAY, time(13, 0), MADRID)
    lunch_end = local_to_utc(MONDAY, time(15, 0), MADRID)
    assert not any(lunch_start <= slot.starts_at < lunch_end for slot in slots)


def test_max_advance_days_discards_the_block_crossing_the_cutoff_whole() -> None:
    """max_advance_days recorta por día natural, no por horas planas -- así que el
    corte cae siempre a medianoche local, y una AvailabilityRule normal nunca lo cruza a
    mitad de bloque (el CheckConstraint le impide cruzar medianoche). Lo que sí puede
    cruzarlo es una apertura extra puntual, y aquí se comprueba que el bloque que se
    solaparía con el corte se descarta entero, no se acorta."""
    appointment_type = _appointment_type(max_advance_days=0)
    now = local_to_utc(MONDAY, time(20, 0), MADRID)
    overnight_opening = _exception(
        starts_at=local_to_utc(MONDAY, time(22, 0), MADRID),
        ends_at=local_to_utc(MONDAY + timedelta(days=1), time(2, 0), MADRID),
        is_available=True,
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[],
        exceptions=[overnight_opening],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY + timedelta(days=1),
        now=now,
        tz=MADRID,
    )

    midnight = local_to_utc(MONDAY + timedelta(days=1), time(0, 0), MADRID)
    assert len(slots) == 4  # 22:00-00:00, cuatro bloques de 30 min
    assert all(slot.ends_at <= midnight for slot in slots)


def test_buffer_from_two_bookings_merges_and_eats_the_gap_between_them() -> None:
    appointment_type = _appointment_type()
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(14, 0))
    booking_a = _booking(
        local_to_utc(MONDAY, time(10, 0), MADRID),
        local_to_utc(MONDAY, time(10, 30), MADRID),
        buffer_minutes=15,
    )
    booking_b = _booking(
        local_to_utc(MONDAY, time(11, 0), MADRID),
        local_to_utc(MONDAY, time(11, 30), MADRID),
        buffer_minutes=15,
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[booking_a, booking_b],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    first_free = local_to_utc(MONDAY, time(11, 45), MADRID)
    assert slots[0].starts_at == first_free
    # El hueco 10:45-11:00 que existiría sin buffer desaparece: los dos colchones lo cubren.
    assert not any(
        local_to_utc(MONDAY, time(10, 45), MADRID) <= slot.starts_at < first_free for slot in slots
    )


def test_back_to_back_bookings_leave_no_phantom_gap() -> None:
    appointment_type = _appointment_type()
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(14, 0))
    booking_a = _booking(
        local_to_utc(MONDAY, time(10, 0), MADRID), local_to_utc(MONDAY, time(10, 30), MADRID)
    )
    booking_b = _booking(
        local_to_utc(MONDAY, time(10, 30), MADRID), local_to_utc(MONDAY, time(11, 0), MADRID)
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[booking_a, booking_b],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    boundary = local_to_utc(MONDAY, time(11, 0), MADRID)
    assert slots[0].starts_at == boundary
    assert all(slot.starts_at >= boundary for slot in slots)


def test_blocking_exception_shrinks_a_rule_block_from_one_side() -> None:
    appointment_type = _appointment_type()
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(14, 0))
    block = _exception(
        starts_at=local_to_utc(MONDAY, time(10, 0), MADRID),
        ends_at=local_to_utc(MONDAY, time(11, 0), MADRID),
        is_available=False,
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[block],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    assert slots[0].starts_at == local_to_utc(MONDAY, time(11, 0), MADRID)


def test_blocking_exception_covering_the_whole_rule_leaves_no_slots() -> None:
    appointment_type = _appointment_type()
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(14, 0))
    block = _exception(
        starts_at=local_to_utc(MONDAY, time(9, 0), MADRID),
        ends_at=local_to_utc(MONDAY, time(15, 0), MADRID),
        is_available=False,
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[block],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    assert slots == []


def test_a_booking_also_carves_into_an_extra_opening_exception() -> None:
    """La resta de reservas ocurre después de fundir reglas + aperturas extra en un
    único conjunto -- así que también afecta a una apertura extra, no solo al horario
    habitual."""
    appointment_type = _appointment_type()
    opening = _exception(
        starts_at=local_to_utc(SATURDAY, time(9, 0), MADRID),
        ends_at=local_to_utc(SATURDAY, time(12, 0), MADRID),
        is_available=True,
    )
    booking = _booking(
        local_to_utc(SATURDAY, time(10, 0), MADRID), local_to_utc(SATURDAY, time(10, 30), MADRID)
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[],  # sábado, sin regla habitual
        exceptions=[opening],
        bookings=[booking],
        window_start=SATURDAY,
        window_end=SATURDAY,
        now=_well_before(SATURDAY),
        tz=MADRID,
    )

    starts = [slot.starts_at for slot in slots]
    assert len(slots) == 5  # 3h de apertura menos 30 min de reserva = 2h30, cinco slots
    assert local_to_utc(SATURDAY, time(10, 0), MADRID) not in starts


def test_an_inactive_rule_produces_no_slots_even_if_the_weekday_matches() -> None:
    appointment_type = _appointment_type()
    inactive_saturday_rule = _rule(
        weekday=SATURDAY.weekday(),
        starts_at_local=time(10, 0),
        ends_at_local=time(13, 0),
        is_active=False,
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[inactive_saturday_rule],
        exceptions=[],
        bookings=[],
        window_start=SATURDAY,
        window_end=SATURDAY,
        now=_well_before(SATURDAY),
        tz=MADRID,
    )

    assert slots == []


def test_zero_notice_keeps_a_slot_starting_exactly_now() -> None:
    appointment_type = _appointment_type(min_notice_hours=0)
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(11, 0))

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=local_to_utc(MONDAY, time(10, 0), MADRID),
        tz=MADRID,
    )

    assert slots[0].starts_at == local_to_utc(MONDAY, time(10, 0), MADRID)


def test_zero_notice_discards_a_slot_that_started_a_moment_ago() -> None:
    appointment_type = _appointment_type(min_notice_hours=0)
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(11, 0))

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=local_to_utc(MONDAY, time(10, 0), MADRID) + timedelta(microseconds=1),
        tz=MADRID,
    )

    assert slots[0].starts_at == local_to_utc(MONDAY, time(10, 30), MADRID)


def test_cancelled_bookings_are_ignored_entirely() -> None:
    appointment_type = _appointment_type()
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(11, 0))
    cancelled = _booking(
        local_to_utc(MONDAY, time(10, 0), MADRID),
        local_to_utc(MONDAY, time(11, 0), MADRID),
        buffer_minutes=120,
        status="cancelled",
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[cancelled],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    assert len(slots) == 2  # el bloqueo entero se ignora, quedan las dos mitades de la hora


def test_each_booking_widens_by_its_own_buffer_not_the_queried_types() -> None:
    """Fija la decisión del BookingWithBuffer: el colchón que aplica es el de la
    reserva ya existente, no el del tipo de cita que se está consultando ahora -- el
    calendario es único y compartido entre tipos."""
    appointment_type = _appointment_type()  # su buffer_minutes no se lee en absoluto
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(14, 0))
    booking_from_another_type = _booking(
        local_to_utc(MONDAY, time(11, 0), MADRID),
        local_to_utc(MONDAY, time(11, 30), MADRID),
        buffer_minutes=60,  # el buffer de SU tipo, no el de appointment_type
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[booking_from_another_type],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    cutoff = local_to_utc(MONDAY, time(12, 30), MADRID)  # 11:00-60min .. 11:30+60min
    assert cutoff in [slot.starts_at for slot in slots]
    assert not any(slot.starts_at < cutoff for slot in slots)


def test_a_perfectly_divisible_block_leaves_no_remainder() -> None:
    appointment_type = _appointment_type(duration_minutes=30)
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(13, 0))

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    assert len(slots) == 6
    assert slots[-1].ends_at == local_to_utc(MONDAY, time(13, 0), MADRID)


def test_a_remainder_shorter_than_the_duration_is_discarded() -> None:
    appointment_type = _appointment_type(duration_minutes=30)
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(13, 15))

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    assert len(slots) == 6  # los 15 min sobrantes (13:00-13:15) no llegan a un bloque
    assert slots[-1].ends_at == local_to_utc(MONDAY, time(13, 0), MADRID)


def test_spring_forward_day_with_ordinary_office_hours_is_unaffected() -> None:
    """El día tiene 23 horas reales, pero un horario de oficina normal (nunca toca
    02:00-04:00) no lo nota: local_to_utc ya resuelve el salto, y aquí solo se confirma
    que el troceo no se entera de nada raro."""
    appointment_type = _appointment_type()
    rule = _rule(
        weekday=SPRING_FORWARD.weekday(), starts_at_local=time(10, 0), ends_at_local=time(14, 0)
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[],
        window_start=SPRING_FORWARD,
        window_end=SPRING_FORWARD,
        now=_well_before(SPRING_FORWARD),
        tz=MADRID,
    )

    assert len(slots) == 8


def test_fall_back_day_with_ordinary_office_hours_is_unaffected() -> None:
    appointment_type = _appointment_type()
    rule = _rule(
        weekday=FALL_BACK.weekday(), starts_at_local=time(10, 0), ends_at_local=time(14, 0)
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[],
        window_start=FALL_BACK,
        window_end=FALL_BACK,
        now=_well_before(FALL_BACK),
        tz=MADRID,
    )

    assert len(slots) == 8


def test_a_single_day_window_works() -> None:
    appointment_type = _appointment_type()
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(11, 0))

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    assert len(slots) == 2


def test_window_start_after_window_end_raises() -> None:
    appointment_type = _appointment_type()

    with pytest.raises(ValueError, match="window_start"):
        compute_free_slots(
            appointment_type=appointment_type,
            rules=[],
            exceptions=[],
            bookings=[],
            window_start=MONDAY,
            window_end=MONDAY - timedelta(days=1),
            now=_well_before(MONDAY),
            tz=MADRID,
        )


def test_a_booking_that_starts_the_day_before_still_blocks_by_real_overlap() -> None:
    """El recorte depende del solape real de instantes UTC, no de a qué fecha
    "pertenece" la reserva -- aquí empieza el día anterior y sigue bloqueando el
    principio de la ventana pedida."""
    appointment_type = _appointment_type()
    rule = _rule(starts_at_local=time(10, 0), ends_at_local=time(14, 0))
    spillover_booking = _booking(
        local_to_utc(MONDAY - timedelta(days=1), time(23, 0), MADRID),
        local_to_utc(MONDAY, time(10, 15), MADRID),
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[rule],
        exceptions=[],
        bookings=[spillover_booking],
        window_start=MONDAY,
        window_end=MONDAY,
        now=_well_before(MONDAY),
        tz=MADRID,
    )

    assert slots[0].starts_at == local_to_utc(MONDAY, time(10, 15), MADRID)


def test_a_rule_crossing_the_spring_forward_gap_loses_the_skipped_hour() -> None:
    """El modelo no prohíbe una AvailabilityRule que cruce 02:00-04:00 -- nadie la usa
    hoy, pero si alguna vez existiera, el troceo tiene que usar aritmética UTC
    acumulativa (no reproyectar cada bloque con local_to_utc) para no duplicar ni saltar
    la hora que no existe esa noche."""
    appointment_type = _appointment_type(duration_minutes=30)
    odd_rule = _rule(
        weekday=SPRING_FORWARD.weekday(), starts_at_local=time(1, 0), ends_at_local=time(4, 30)
    )

    slots = compute_free_slots(
        appointment_type=appointment_type,
        rules=[odd_rule],
        exceptions=[],
        bookings=[],
        window_start=SPRING_FORWARD,
        window_end=SPRING_FORWARD,
        now=_well_before(SPRING_FORWARD),
        tz=MADRID,
    )

    # 1:00 a 4:30 de reloj de pared son 3h30 nominales, pero esa noche se saltan 60
    # minutos reales -- quedan 2h30 reales, cinco bloques de 30 min, no siete.
    assert len(slots) == 5
