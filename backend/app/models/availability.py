"""Las dos mitades de "cuándo se me puede reservar".

Están guardadas a propósito en tipos distintos, y los nombres de las columnas lo dicen:

- AvailabilityRule.starts_at_local es un TIME naive más un día de la semana. "Los lunes a
  partir de las 10:00" es una intención que tiene que seguir significando las 10:00 en
  enero y en julio; guardada como un instante, el cambio de hora semestral la movería.
- AvailabilityException.starts_at es un TIMESTAMPTZ. "Bloqueado del 15 al 30 de agosto" es
  un tramo concreto de la línea temporal, no una intención recurrente.

La proyección de lo primero a lo segundo vive en app/core/timezone.py: local_to_utc()
convierte una regla en instantes reales de una fecha dada, y local_day_bounds() es lo que
significa de verdad "bloquear el 15 entero" una vez escrito.
"""

from datetime import datetime, time

from sqlalchemy import CheckConstraint, DateTime, String, Time, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import TimestampMixin


class AvailabilityRule(TimestampMixin, Base):
    """Un bloque recurrente de la semana laboral, en el reloj de pared local del dueño.

    En la práctica, diez filas: de lunes a viernes, mañanas y tardes. No hay
    appointment_type_id -- un dueño y un calendario, así que el horario es global y cada
    tipo de reunión se recorta sobre las mismas horas.
    """

    __tablename__ = "availability_rule"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 0 = lunes, igual que date.weekday(), así que proyectar una regla sobre una fecha no
    # necesita ninguna aritmética. El EXTRACT(DOW) de Postgres es 0 = domingo; aquí no se
    # usa en ningún sitio.
    weekday: Mapped[int] = mapped_column()
    # TIME WITHOUT TIME ZONE. El sufijo _local es un aviso de que esto no es un instante y
    # no se puede comparar directamente contra uno.
    starts_at_local: Mapped[time] = mapped_column(Time)
    ends_at_local: Mapped[time] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        # Descarta también un bloque que cruce la medianoche ("22:00-02:00"), que es lo
        # correcto para un horario profesional y evita que la proyección tenga que partir
        # una regla en dos días naturales.
        CheckConstraint("ends_at_local > starts_at_local", name="local_range_ordered"),
        # La clave natural, que es lo que permite al seed insertar solo lo que falta. Los
        # bloques solapados el mismo día (10-14 y 12-16) siguen permitidos: producen la
        # unión de los huecos, que es inofensiva, y prohibirlos exigiría una restricción
        # EXCLUDE y la extensión btree_gist para nada.
        UniqueConstraint("weekday", "starts_at_local"),
    )

    # Sin índice. Esta tabla tiene diez filas; un escaneo secuencial es el plan correcto y
    # un índice solo sería una cosa más que mantener al día en cada migración.

    def __repr__(self) -> str:
        return f"<AvailabilityRule {self.weekday} {self.starts_at_local}-{self.ends_at_local}>"


class AvailabilityException(TimestampMixin, Base):
    """Una excepción puntual al horario semanal, como intervalo UTC real.

    is_available lleva las dos direcciones a propósito:

    - False -- un bloqueo: un festivo, un viaje, una tarde libre. Es el caso habitual.
    - True  -- una apertura extra fuera de las reglas semanales: un sábado por la mañana
      acordado con un cliente concreto.

    Ambas desde el primer día porque es un único booleano; añadir la segunda dirección más
    tarde sería una migración.
    """

    __tablename__ = "availability_exception"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Indexada porque la consulta de disponibilidad filtra las excepciones por solape
    # contra la ventana pedida, y este es el lado por el que puede buscar.
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_available: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    # Solo para administración -- "Médico", "Vacaciones". No puede aparecer nunca en una
    # respuesta pública: a la página de reservas se le dice que un hueco no está libre,
    # nunca por qué.
    reason: Mapped[str | None] = mapped_column(String(200), default=None)

    __table_args__ = (CheckConstraint("ends_at > starts_at", name="range_ordered"),)

    def __repr__(self) -> str:
        kind = "open" if self.is_available else "blocked"
        return f"<AvailabilityException {kind} {self.starts_at} -> {self.ends_at}>"
