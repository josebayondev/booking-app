"""Todos los modelos mapeados, sin excepción.

Importar aquí cada modelo no es orden, es funcional. alembic/env.py hace
`from app.models import Base` y autogenerate solo ve las tablas cuyo módulo se ha
importado de verdad, así que un modelo que falte en este fichero produce una migración
*vacía* sin avisar de nada. tests/test_models_domain.py fija el conjunto para que ese
fallo no pueda ocurrir en silencio.
"""

from app.models.appointment_type import AppointmentType
from app.models.availability import AvailabilityException, AvailabilityRule
from app.models.base import Base
from app.models.mixins import TimestampMixin

__all__ = [
    "AppointmentType",
    "AvailabilityException",
    "AvailabilityRule",
    "Base",
    "TimestampMixin",
]
