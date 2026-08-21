"""Conversions between the owner's local wall clock and UTC.

Every instant in this project is stored in UTC. The owner, however, thinks in local
wall-clock time: "Mondays from 10:00 to 14:00" has to keep meaning 10:00 in January
and 10:00 in July. Stored as 09:00Z it would silently become 11:00 local once summer
time starts.

That is why availability rules keep a naive local time plus a weekday, and the
conversion to a real instant happens here, against a concrete date -- zoneinfo then
applies whichever offset was in force on that day.

This module is the single place where that conversion lives, so the twice-a-year
daylight-saving edge cases are covered by one small set of tests instead of being
spread across the codebase.
"""

from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.core.config import get_settings


@lru_cache
def booking_timezone() -> ZoneInfo:
    """The owner's timezone, from settings. One owner, one calendar, so it is
    configuration and not a column.

    Cached because ZoneInfo parses the tz database on construction and this is called
    once per slot computation.
    """
    return ZoneInfo(get_settings().booking_timezone)


def utc_now() -> datetime:
    """The clock, always aware and in UTC.

    Exists so callers can take it as an argument and tests can substitute a fixed
    instant, and so nobody reaches for datetime.utcnow(), which returns a *naive*
    datetime that compares wrongly against every aware one in this codebase.
    """
    return datetime.now(UTC)


def local_to_utc(day: date, wall: time, tz: ZoneInfo | None = None) -> datetime:
    """The instant at which a local wall-clock time occurs on a given date.

    "10:00 on Monday the 7th, in Madrid" -> the matching UTC instant. This is what
    turns a recurring availability rule into a real bookable slot.

    Both daylight-saving pathologies resolve deterministically via fold=0, and are
    pinned by tests:

    - Ambiguous time (last Sunday of October, 02:30 happens twice): the first pass is
      chosen.
    - Nonexistent time (last Sunday of March, 02:30 never happens): it is read with
      the offset in force before the jump, so it lands on the instant that is locally
      03:30. Raising would be worse -- no realistic working hours touch 02:00-03:00,
      and an exception there would turn an impossible input into an outage.
    """
    tz = tz or booking_timezone()
    return datetime.combine(day, wall, tzinfo=tz).astimezone(UTC)


def utc_to_local_date(moment: datetime, tz: ZoneInfo | None = None) -> date:
    """The local calendar day an instant belongs to.

    Needed to group slots for the UI: 2026-09-01T22:30Z is already the 2nd in Madrid,
    and grouping by the UTC date would file it under the wrong day of the calendar.
    """
    tz = tz or booking_timezone()
    return moment.astimezone(tz).date()


def local_day_bounds(day: date, tz: ZoneInfo | None = None) -> tuple[datetime, datetime]:
    """Half-open [start, end) UTC bounds of a local calendar day.

    What "block the whole of August 15th" actually means. Derived from both midnights
    rather than by adding 24 hours, because on the days the clocks change a local day
    is 23 or 25 real hours long.
    """
    tz = tz or booking_timezone()
    start = local_to_utc(day, time.min, tz)
    end = local_to_utc(day + timedelta(days=1), time.min, tz)
    return start, end
