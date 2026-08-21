"""Tests de las conversiones de zona horaria, incluidos los dos cambios de hora del año:
la hora que no existe en marzo y la que ocurre dos veces en octubre."""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from app.core.timezone import (
    booking_timezone,
    local_day_bounds,
    local_to_utc,
    utc_now,
    utc_to_local_date,
)

MADRID = ZoneInfo("Europe/Madrid")

# Los dos domingos al año en que se mueve el reloj en la UE. Escritos a mano en vez de
# calculados para que los tests de abajo comprueben contra fechas que ha verificado una
# persona.
SPRING_FORWARD = date(2026, 3, 29)  # 02:00 CET -> 03:00 CEST, las 02:00-02:59 no existen
FALL_BACK = date(2026, 10, 25)  # 03:00 CEST -> 02:00 CET, las 02:00-02:59 pasan dos veces


def test_ten_in_the_morning_stays_ten_in_the_morning() -> None:
    """El motivo de que las reglas de disponibilidad guarden hora de pared y no un instante.

    La misma regla -- "10:00" -- cae en un instante UTC distinto en invierno y en verano. De
    haberse guardado como 09:00Z, se habría desplazado a las 11:00 locales en cuanto
    empezase el horario de verano.
    """
    assert local_to_utc(date(2026, 1, 15), time(10, 0), MADRID) == datetime(
        2026, 1, 15, 9, 0, tzinfo=UTC
    )
    assert local_to_utc(date(2026, 7, 15), time(10, 0), MADRID) == datetime(
        2026, 7, 15, 8, 0, tzinfo=UTC
    )


def test_nonexistent_local_time_resolves_instead_of_raising() -> None:
    """Las 02:30 no existen el día en que se adelanta el reloj.

    fold=0 las lee con el desfase vigente antes del salto (CET, +1), así que caen en el
    instante que localmente son las 03:30. Determinista y documentado: ningún horario
    laboral realista toca esa hora, y lanzar una excepción convertiría una entrada imposible
    en una caída.
    """
    moment = local_to_utc(SPRING_FORWARD, time(2, 30), MADRID)

    assert moment == datetime(2026, 3, 29, 1, 30, tzinfo=UTC)
    assert moment.astimezone(MADRID).hour == 3


def test_ambiguous_local_time_picks_the_first_pass() -> None:
    """Las 02:30 pasan dos veces el día en que se atrasa el reloj; fold=0 elige la primera
    (CEST)."""
    moment = local_to_utc(FALL_BACK, time(2, 30), MADRID)

    assert moment == datetime(2026, 10, 25, 0, 30, tzinfo=UTC)


def test_late_evening_utc_belongs_to_the_next_local_day() -> None:
    """Agrupar los huecos por su fecha UTC archivaría este en el día equivocado."""
    assert utc_to_local_date(datetime(2026, 9, 1, 22, 30, tzinfo=UTC), MADRID) == date(2026, 9, 2)


def test_local_day_bounds_span_a_whole_local_day() -> None:
    start, end = local_day_bounds(date(2026, 9, 1), MADRID)

    assert start == datetime(2026, 8, 31, 22, 0, tzinfo=UTC)
    assert end == datetime(2026, 9, 1, 22, 0, tzinfo=UTC)
    assert utc_to_local_date(start, MADRID) == date(2026, 9, 1)


def test_local_day_bounds_follow_the_clock_change() -> None:
    """Un día local no siempre dura 24 horas, que es justo por lo que los límites se derivan
    de las dos medianoches en vez de sumando 24 horas fijas."""
    spring_start, spring_end = local_day_bounds(SPRING_FORWARD, MADRID)
    fall_start, fall_end = local_day_bounds(FALL_BACK, MADRID)

    assert (spring_end - spring_start).total_seconds() == 23 * 3600
    assert (fall_end - fall_start).total_seconds() == 25 * 3600


def test_everything_returned_is_timezone_aware() -> None:
    """Un solo datetime naive que se escapase de aquí se compararía mal contra todos los
    conscientes de zona del código, y el fallo saldría lejos de la causa."""
    assert utc_now().tzinfo is not None
    assert local_to_utc(date(2026, 9, 1), time(10, 0), MADRID).tzinfo is not None

    start, end = local_day_bounds(date(2026, 9, 1), MADRID)
    assert start.tzinfo is not None
    assert end.tzinfo is not None


def test_timezone_defaults_to_the_configured_one() -> None:
    """Llamados sin tz explícita, los helpers leen Settings.booking_timezone."""
    assert booking_timezone() == MADRID
    assert local_to_utc(date(2026, 1, 15), time(10, 0)) == datetime(2026, 1, 15, 9, 0, tzinfo=UTC)
