"""La reserva: el hueco real del calendario, con su acceso público por token opaco."""

import secrets
import string
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin

# secrets.token_urlsafe(32) produce siempre 43 caracteres (32 bytes en base64 urlsafe sin
# relleno).
_TOKEN_LENGTH = 43

_REFERENCE_ALPHABET = string.ascii_uppercase + string.digits


def _generate_reference() -> str:
    """El prefijo BK- más seis caracteres al azar (mayúsculas y dígitos), p. ej. BK-7F3K2Q.

    A diferencia del token, esto no protege nada -- es lo que se puede decir en voz alta o
    citar en un email ("tu referencia es BK-7F3K2Q") sin regalar acceso a la reserva.
    """
    suffix = "".join(secrets.choice(_REFERENCE_ALPHABET) for _ in range(6))
    return f"BK-{suffix}"


class Booking(TimestampMixin, Base):
    """Una reserva del calendario público.

    Nace en confirmed y no en pending: un estado intermedio abandonado seguiría
    bloqueando el hueco -- el EXCLUDE de abajo no distingue pendiente de confirmado -- y
    obligaría a purgar reservas fantasma. cancelled es el único destino posterior; no hay
    tabla de reprogramaciones, PR 7 reprograma cancelando y creando una reserva nueva.

    starts_at/ends_at guardan la reunión real, sin el buffer_minutes de su
    appointment_type: ese colchón se aplica solo al calcular huecos libres (ver
    AppointmentType.buffer_minutes), para que el email de confirmación cite la hora
    verdadera de la reunión y cambiar el colchón no exija reescribir reservas ya hechas.
    """

    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(primary_key=True)
    # La clave de acceso pública, y la única forma de llegar a una reserva sin pasar por
    # el panel de administración. secrets.token_urlsafe y no un id secuencial: adivinar un
    # id consecutivo daría acceso a la reserva de otra persona (IDOR).
    token: Mapped[str] = mapped_column(
        String(_TOKEN_LENGTH), unique=True, default=lambda: secrets.token_urlsafe(32)
    )
    # La referencia humana -- la que se puede decir por teléfono o citar en un email sin
    # regalar el acceso que sí da el token.
    reference: Mapped[str] = mapped_column(String(9), unique=True, default=_generate_reference)
    # Sin ondelete propio: no hay ninguna vía todavía para borrar un tipo de cita con
    # reservas, y el NO ACTION por defecto de Postgres es justo lo que se quiere mientras
    # tanto -- que el borrado falle en vez de dejar reservas huérfanas.
    appointment_type_id: Mapped[int] = mapped_column(ForeignKey("appointment_type.id"))
    customer_name: Mapped[str] = mapped_column(String(200))
    customer_email: Mapped[str] = mapped_column(String(255))
    # TIMESTAMPTZ, como toda marca de tiempo del proyecto. Indexada porque calcular huecos
    # libres (PR 4) filtra las reservas por solape contra la ventana pedida.
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # VARCHAR + CHECK y no un enum nativo de Postgres: ALTER TYPE ... ADD VALUE no corre
    # dentro de una transacción, y Alembic envuelve cada migración en una.
    status: Mapped[str] = mapped_column(
        String(20), default="confirmed", server_default=text("'confirmed'")
    )

    __table_args__ = (
        CheckConstraint("status IN ('confirmed', 'cancelled')", name="status_allowed"),
        CheckConstraint("ends_at > starts_at", name="range_ordered"),
        # La restricción que de verdad impide la doble reserva, a nivel de base de datos y
        # no solo de aplicación -- así que sobrevive a una condición de carrera entre dos
        # peticiones concurrentes. No hace falta btree_gist: con un solo profesional el
        # EXCLUDE va sobre un único tstzrange, sin columna de igualdad que acompañar, así
        # que basta el soporte nativo de rangos de Postgres.
        #
        # WHERE status <> 'cancelled' es lo que permite volver a reservar un hueco que se
        # canceló: una reserva cancelada no compite por el hueco.
        ExcludeConstraint(
            (func.tstzrange(starts_at, ends_at, "[)"), "&&"),
            where=(status != "cancelled"),
            name="no_overlapping_bookings",
        ),
    )

    def __repr__(self) -> str:
        return f"<Booking {self.reference} {self.status} {self.starts_at}>"
