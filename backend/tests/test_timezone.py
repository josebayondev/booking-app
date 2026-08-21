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

# The two Sundays a year the clocks move in the EU. Spelled out rather than computed
# so the tests below assert against dates a human has checked.
SPRING_FORWARD = date(2026, 3, 29)  # 02:00 CET -> 03:00 CEST, 02:00-02:59 never happens
FALL_BACK = date(2026, 10, 25)  # 03:00 CEST -> 02:00 CET, 02:00-02:59 happens twice


def test_ten_in_the_morning_stays_ten_in_the_morning() -> None:
    """The reason availability rules store wall-clock time and not an instant.

    The same rule -- "10:00" -- lands on a different UTC instant in winter and in
    summer. Had it been stored as 09:00Z, it would have drifted to 11:00 local once
    summer time started.
    """
    assert local_to_utc(date(2026, 1, 15), time(10, 0), MADRID) == datetime(
        2026, 1, 15, 9, 0, tzinfo=UTC
    )
    assert local_to_utc(date(2026, 7, 15), time(10, 0), MADRID) == datetime(
        2026, 7, 15, 8, 0, tzinfo=UTC
    )


def test_nonexistent_local_time_resolves_instead_of_raising() -> None:
    """02:30 does not exist on the spring-forward day.

    fold=0 reads it with the offset in force before the jump (CET, +1), so it lands
    on the instant that is locally 03:30. Deterministic and documented: no realistic
    working hours touch that hour, and raising would turn an impossible input into an
    outage.
    """
    moment = local_to_utc(SPRING_FORWARD, time(2, 30), MADRID)

    assert moment == datetime(2026, 3, 29, 1, 30, tzinfo=UTC)
    assert moment.astimezone(MADRID).hour == 3


def test_ambiguous_local_time_picks_the_first_pass() -> None:
    """02:30 happens twice on the fall-back day; fold=0 means the earlier one (CEST)."""
    moment = local_to_utc(FALL_BACK, time(2, 30), MADRID)

    assert moment == datetime(2026, 10, 25, 0, 30, tzinfo=UTC)


def test_late_evening_utc_belongs_to_the_next_local_day() -> None:
    """Grouping slots by their UTC date would file this one under the wrong day."""
    assert utc_to_local_date(datetime(2026, 9, 1, 22, 30, tzinfo=UTC), MADRID) == date(2026, 9, 2)


def test_local_day_bounds_span_a_whole_local_day() -> None:
    start, end = local_day_bounds(date(2026, 9, 1), MADRID)

    assert start == datetime(2026, 8, 31, 22, 0, tzinfo=UTC)
    assert end == datetime(2026, 9, 1, 22, 0, tzinfo=UTC)
    assert utc_to_local_date(start, MADRID) == date(2026, 9, 1)


def test_local_day_bounds_follow_the_clock_change() -> None:
    """A local day is not always 24 hours, which is why the bounds are derived from
    both midnights instead of by adding a fixed 24 hours."""
    spring_start, spring_end = local_day_bounds(SPRING_FORWARD, MADRID)
    fall_start, fall_end = local_day_bounds(FALL_BACK, MADRID)

    assert (spring_end - spring_start).total_seconds() == 23 * 3600
    assert (fall_end - fall_start).total_seconds() == 25 * 3600


def test_everything_returned_is_timezone_aware() -> None:
    """A single naive datetime escaping here would compare wrongly against every
    aware one in the codebase, and the failure would surface far from the cause."""
    assert utc_now().tzinfo is not None
    assert local_to_utc(date(2026, 9, 1), time(10, 0), MADRID).tzinfo is not None

    start, end = local_day_bounds(date(2026, 9, 1), MADRID)
    assert start.tzinfo is not None
    assert end.tzinfo is not None


def test_timezone_defaults_to_the_configured_one() -> None:
    """Called without an explicit tz, the helpers read Settings.booking_timezone."""
    assert booking_timezone() == MADRID
    assert local_to_utc(date(2026, 1, 15), time(10, 0)) == datetime(2026, 1, 15, 9, 0, tzinfo=UTC)
