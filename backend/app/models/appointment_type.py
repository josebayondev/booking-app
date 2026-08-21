from sqlalchemy import CheckConstraint, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin


class AppointmentType(TimestampMixin, Base):
    """A kind of meeting that can be booked, with the policy that governs it.

    There is one row today ("Reunion inicial", 30 minutes). The table exists anyway
    because the alternative -- constants in the code -- would make every change to the
    duration or the notice period a deploy, and because the admin panel (15.3) needs
    somewhere to write them.

    Every policy number here is deliberately data and not structure: they are the values
    that get tuned after the first few real bookings, and tuning them must never require
    a migration.
    """

    __tablename__ = "appointment_type"

    # Never serialized. The public API addresses appointment types by slug, and bookings
    # by their opaque token, so no sequential id ever reaches a client.
    id: Mapped[int] = mapped_column(primary_key=True)
    # The natural key. It is what makes the seed idempotent (see app/seed.py) and what
    # the API will expose, so it is stable and human-readable: "reunion-inicial".
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    duration_minutes: Mapped[int] = mapped_column()
    # Dead time kept clear on both sides of a meeting. Not folded into the booking's
    # ends_at on purpose: that column has to keep saying when the meeting really ends,
    # because it is what the confirmation email quotes. The buffer is applied when free
    # slots are computed, by widening each busy interval -- which also means changing it
    # here takes effect on the next request, with no data to rewrite.
    buffer_minutes: Mapped[int] = mapped_column(default=15, server_default=text("15"))
    # How soon before a meeting it can still be booked. Twelve hours rather than
    # twenty-four so that booking in the evening still leaves tomorrow available.
    min_notice_hours: Mapped[int] = mapped_column(default=12, server_default=text("12"))
    max_advance_days: Mapped[int] = mapped_column(default=60, server_default=text("60"))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    # Named by hand, every one of them: the "ck" naming convention in base.py is built on
    # constraint_name, so an unnamed CheckConstraint fails when the migration is
    # generated. That is the point -- a violation then reports
    # ck_appointment_type_duration_range instead of an opaque generated name.
    __table_args__ = (
        CheckConstraint("duration_minutes BETWEEN 5 AND 480", name="duration_range"),
        CheckConstraint("buffer_minutes BETWEEN 0 AND 240", name="buffer_range"),
        CheckConstraint("min_notice_hours >= 0", name="min_notice_non_negative"),
        CheckConstraint("max_advance_days BETWEEN 1 AND 365", name="max_advance_range"),
    )

    def __repr__(self) -> str:
        return f"<AppointmentType {self.slug} ({self.duration_minutes}min)>"
