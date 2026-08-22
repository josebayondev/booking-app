"""Contrato de entrada y salida de GET /api/v1/availability."""

from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

# 13.1 en ClickUp: nadie necesita pedir años de disponibilidad, y el free tier de Render
# no lo aguantaría -- un rango sin tope fuerza un bucle diario enorme en
# compute_free_slots por pura entrada de query param.
MAX_RANGE_DAYS = 62


class AvailabilityQuery(BaseModel):
    """Los parámetros de consulta de GET /api/v1/availability.

    Los alias (type/from/to) son los nombres que pide 13.1 para la URL pública; los
    nombres de atributo son distintos porque `from` es palabra reservada en Python.

    date_from y date_to son fechas locales (el día que ve quien reserva), no instantes
    -- la conversión a los límites UTC reales del rango la hace el router con
    local_day_bounds(), nunca esta clase.
    """

    appointment_type: str = Field(alias="type")
    date_from: date = Field(alias="from")
    date_to: date = Field(alias="to")

    @model_validator(mode="after")
    def check_range_is_not_reversed(self) -> Self:
        if self.date_to < self.date_from:
            raise ValueError("date_to no puede ser anterior a date_from")
        return self

    @model_validator(mode="after")
    def check_range_is_not_too_large(self) -> Self:
        if (self.date_to - self.date_from).days > MAX_RANGE_DAYS:
            raise ValueError(f"el rango no puede superar los {MAX_RANGE_DAYS} días")
        return self


class FreeSlotOut(BaseModel):
    starts_at: datetime
    ends_at: datetime


class DayAvailabilityOut(BaseModel):
    """Un día del rango pedido, con sus huecos -- vacío si ese día no tiene ninguno.

    Se incluye todo día entre date_from y date_to aunque no tenga huecos (fin de semana,
    fuera de la ventana de antelación máxima...) para que el frontend pinte el mes de un
    tirón sin tener que rellenar los huecos que faltan.
    """

    date: date
    slots: list[FreeSlotOut]
