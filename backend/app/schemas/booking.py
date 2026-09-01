"""Contrato de entrada y salida de POST /api/v1/bookings."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookingCreate(BaseModel):
    """Lo que manda el visitante para reservar: el hueco exacto que ya vio libre en
    GET /availability, más quién es.

    `starts_at` tiene que llegar con offset -- comparar un instante naive contra los
    slots ya calculados (conscientes de zona) revienta en Python con un TypeError en vez
    de fallar con un error legible, así que se rechaza aquí, en el borde. `ends_at` no se
    pide: lo calcula el router a partir de `duration_minutes` del tipo de cita, para no
    confiar en un cliente que podría mandar una duración distinta a la contratada.
    """

    appointment_type: str = Field(alias="type")
    starts_at: datetime
    customer_name: str = Field(min_length=1, max_length=200)
    customer_email: str = Field(min_length=3, max_length=255)

    @field_validator("starts_at")
    @classmethod
    def starts_at_must_have_offset(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("starts_at debe incluir la zona horaria (offset ISO 8601)")
        return value

    @field_validator("customer_email")
    @classmethod
    def customer_email_must_look_like_one(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("customer_email no parece un email válido")
        return value


class BookingOut(BaseModel):
    """La confirmación: el token para el enlace de gestión y la referencia para citar en
    voz alta o por email, sin regalar acceso a la reserva (ver app/models/booking.py)."""

    model_config = ConfigDict(from_attributes=True)

    token: str
    reference: str
    starts_at: datetime
    ends_at: datetime


class BookingDetailOut(BaseModel):
    """La vista completa de una reserva: la página a la que apunta el enlace del email
    (GET /bookings/{token}) y lo que devuelven cancelarla o reprogramarla. Sin
    customer_email -- quien tiene el token ya sabe su propio email, no hace falta
    devolvérselo.

    Lleva tanto el slug (`appointment_type`) como el nombre (`appointment_type_name`): el
    slug es lo que el frontend necesita para pedir `GET /availability` al reprogramar, el
    nombre es lo que se pinta en la página."""

    token: str
    reference: str
    status: str
    starts_at: datetime
    ends_at: datetime
    customer_name: str
    appointment_type: str
    appointment_type_name: str


class BookingReschedule(BaseModel):
    """Lo que manda el cliente para reprogramar: el nuevo hueco, ya visto libre en
    GET /availability. El tipo de cita no cambia, solo el horario -- por eso no lleva
    `type` como BookingCreate."""

    starts_at: datetime

    @field_validator("starts_at")
    @classmethod
    def starts_at_must_have_offset(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("starts_at debe incluir la zona horaria (offset ISO 8601)")
        return value
