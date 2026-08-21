"""Mixins reutilizables por los modelos. Hoy solo el de marcas de tiempo."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """created_at / updated_at para cualquier tabla que los quiera.

    Los rellena la base de datos (server_default / onupdate) y no Python, así que una fila
    escrita desde psql o desde una migración de datos también queda marcada -- esos
    caminos no pasan nunca por el ORM.

    timezone=True se traduce en TIMESTAMPTZ. Todos los instantes de este proyecto se
    guardan en UTC; la conversión a Europe/Madrid ocurre en los bordes, en
    app/core/timezone.py.
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
