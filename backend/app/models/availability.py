"""The two halves of "when can I be booked".

They are deliberately stored in different types, and the column names say so:

- AvailabilityRule.starts_at_local is a naive TIME plus a weekday. "Mondays from 10:00"
  is an intention that must still mean 10:00 in January and in July; stored as an
  instant, the twice-yearly clock change would move it.
- AvailabilityException.starts_at is a TIMESTAMPTZ. "Blocked from the 15th to the 30th
  of August" is a concrete stretch of the timeline, not a recurring intention.

The projection from the first to the second lives in app/core/timezone.py:
local_to_utc() turns a rule into real instants on a given date, and local_day_bounds()
is what "block the whole of the 15th" actually means once written down.
"""

from datetime import datetime, time

from sqlalchemy import CheckConstraint, DateTime, String, Time, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin


class AvailabilityRule(TimestampMixin, Base):
    """One recurring block of the working week, in the owner's local wall clock.

    Ten rows in practice: Monday to Friday, mornings and afternoons. There is no
    appointment_type_id -- one owner, one calendar, so the schedule is global and every
    kind of meeting is carved out of the same hours.
    """

    __tablename__ = "availability_rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 0 = Monday, matching date.weekday(), so projecting a rule onto a date needs no
    # arithmetic. Postgres' own EXTRACT(DOW) is 0 = Sunday; nothing here uses it.
    weekday: Mapped[int] = mapped_column()
    # TIME WITHOUT TIME ZONE. The _local suffix is a warning that this is not an instant
    # and must not be compared against one directly.
    starts_at_local: Mapped[time] = mapped_column(Time)
    ends_at_local: Mapped[time] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        # Also rules out a block crossing midnight ("22:00-02:00"), which is correct for
        # professional working hours and keeps the projection from having to split a
        # rule across two calendar days.
        CheckConstraint("ends_at_local > starts_at_local", name="local_range_ordered"),
        # The natural key, which is what lets the seed insert only what is missing.
        # Overlapping blocks on the same weekday (10-14 and 12-16) are still allowed:
        # they produce the union of the slots, which is harmless, and forbidding them
        # would mean an EXCLUDE constraint and the btree_gist extension for nothing.
        UniqueConstraint("weekday", "starts_at_local"),
    )

    # No index. This table holds ten rows; a sequential scan is the right plan and an
    # index would only be one more thing for a migration to keep in step.

    def __repr__(self) -> str:
        return f"<AvailabilityRule {self.weekday} {self.starts_at_local}-{self.ends_at_local}>"


class AvailabilityException(TimestampMixin, Base):
    """A one-off override of the weekly schedule, as a real UTC interval.

    is_available carries both directions on purpose:

    - False -- a block: a holiday, a trip, an afternoon off. This is the common case.
    - True  -- an extra opening outside the weekly rules: a Saturday morning agreed with
      a particular client.

    Both from day one because it is a single boolean; adding the second direction later
    would be a migration.
    """

    __tablename__ = "availability_exception"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Indexed because the availability query filters exceptions by an overlap against
    # the requested window, and this is the side it can seek on.
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_available: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    # Administration only -- "Medico", "Vacaciones". It must never appear in a public
    # response: the booking page is told that a slot is unavailable, never why.
    reason: Mapped[str | None] = mapped_column(String(200), default=None)

    __table_args__ = (CheckConstraint("ends_at > starts_at", name="range_ordered"),)

    def __repr__(self) -> str:
        kind = "open" if self.is_available else "blocked"
        return f"<AvailabilityException {kind} {self.starts_at} -> {self.ends_at}>"
