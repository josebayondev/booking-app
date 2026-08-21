from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """created_at / updated_at for any table that wants them.

    Both are filled by the database (server_default / onupdate) rather than by Python,
    so a row written from psql or from a data migration is stamped too -- those paths
    never run the ORM.

    timezone=True maps to TIMESTAMPTZ. Every instant in this project is stored in UTC;
    conversion to Europe/Madrid happens at the edges, in app/core/timezone.py.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
