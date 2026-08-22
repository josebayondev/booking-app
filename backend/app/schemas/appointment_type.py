"""Contrato de salida de GET /appointment-types."""

from pydantic import BaseModel, ConfigDict


class AppointmentTypeOut(BaseModel):
    """Lo público de un tipo de cita -- sin su política interna de reservas
    (buffer_minutes, min_notice_hours, max_advance_days, sort_order), que no le hace
    falta a quien solo está eligiendo qué reservar."""

    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    description: str | None
    duration_minutes: int
