"""Contrato de entrada y salida de GET /availability."""

from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, model_validator


class AvailabilityQuery(BaseModel):
    """Los parámetros de consulta de GET /availability.

    date_from y date_to son fechas locales (el día que ve quien reserva), no instantes
    -- la conversión a los límites UTC reales del rango la hace el router con
    local_day_bounds(), nunca esta clase.
    """

    appointment_type: str
    date_from: date
    date_to: date

    @model_validator(mode="after")
    def check_range_is_not_reversed(self) -> Self:
        if self.date_to < self.date_from:
            raise ValueError("date_to no puede ser anterior a date_from")
        return self


class FreeSlotOut(BaseModel):
    starts_at: datetime
    ends_at: datetime
