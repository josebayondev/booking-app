"""El tipo de cita: qué clase de reunión se puede reservar y con qué política."""

from sqlalchemy import CheckConstraint, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin


class AppointmentType(TimestampMixin, Base):
    """Una clase de reunión reservable, junto con la política que la gobierna.

    Hoy hay una sola fila ("Reunión inicial", 30 minutos). La tabla existe igualmente
    porque la alternativa -- constantes en el código -- convertiría cualquier cambio de
    duración o de antelación en un despliegue, y porque el panel de administración (15.3)
    necesita dónde escribirlos.

    Cada número de política de aquí es dato y no estructura a propósito: son los valores
    que se ajustan tras las primeras reservas reales, y ajustarlos no puede exigir nunca
    una migración.
    """

    __tablename__ = "appointment_type"

    # Nunca se serializa. La API pública direcciona los tipos de cita por slug, y las
    # reservas por su token opaco, así que ningún id secuencial llega a un cliente.
    id: Mapped[int] = mapped_column(primary_key=True)
    # La clave natural. Es lo que hace idempotente al seed (ver app/seed.py) y lo que
    # expondrá la API, así que es estable y legible por humanos: "reunion-inicial".
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    duration_minutes: Mapped[int] = mapped_column()
    # Tiempo muerto que se reserva a ambos lados de una reunión. No se mete dentro del
    # ends_at de la reserva a propósito: esa columna tiene que seguir diciendo cuándo
    # termina la reunión de verdad, porque es lo que cita el email de confirmación. El
    # colchón se aplica al calcular los huecos libres, ensanchando cada intervalo ocupado
    # -- lo que además significa que cambiarlo aquí surte efecto en la siguiente petición,
    # sin datos que reescribir.
    buffer_minutes: Mapped[int] = mapped_column(default=15, server_default=text("15"))
    # Con cuánta antelación mínima se puede reservar. Doce horas y no veinticuatro para que
    # reservar por la tarde siga dejando mañana disponible.
    min_notice_hours: Mapped[int] = mapped_column(default=12, server_default=text("12"))
    max_advance_days: Mapped[int] = mapped_column(default=60, server_default=text("60"))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    sort_order: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    # Nombradas a mano, todas: la convención "ck" de base.py se apoya en constraint_name,
    # así que un CheckConstraint sin nombre falla al generar la migración. Y eso es justo
    # lo que se busca -- una violación reporta entonces
    # ck_appointment_type_duration_range en vez de un nombre generado opaco.
    __table_args__ = (
        CheckConstraint("duration_minutes BETWEEN 5 AND 480", name="duration_range"),
        CheckConstraint("buffer_minutes BETWEEN 0 AND 240", name="buffer_range"),
        CheckConstraint("min_notice_hours >= 0", name="min_notice_non_negative"),
        CheckConstraint("max_advance_days BETWEEN 1 AND 365", name="max_advance_range"),
    )

    def __repr__(self) -> str:
        return f"<AppointmentType {self.slug} ({self.duration_minutes}min)>"
