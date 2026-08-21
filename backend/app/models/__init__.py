"""The mapped models, all of them.

Importing every model here is load-bearing, not tidiness. alembic/env.py does
`from app.models import Base` and autogenerate only sees the tables whose module has
actually been imported, so a model missing from this file produces an *empty* migration
without warning about anything. tests/test_models_domain.py pins the set so that failure
cannot happen quietly.
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
