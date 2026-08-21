"""Tests de la convención de nombres de la Base declarativa."""

from app.models import Base
from app.models.base import NAMING_CONVENTION


def test_metadata_carries_the_naming_convention() -> None:
    """Una salvaguarda barata sobre algo cuya ausencia falla en silencio.

    Sin la convención, Postgres bautiza él mismo las restricciones y `alembic check` empieza
    a reportar desviaciones que no existen -- o, peor, deja de resultar fiable. Solo se puede
    fijar mientras el esquema está vacío, así que una refactorización que la quitase sería
    cara de deshacer una vez que hay tablas.
    """
    assert Base.metadata.naming_convention == NAMING_CONVENTION
    assert set(NAMING_CONVENTION) == {"ix", "uq", "ck", "fk", "pk"}


def test_composite_indexes_get_distinct_names() -> None:
    """Por qué la convención usa column_0_N_name y no column_0_name: dos índices compuestos
    que empiecen por la misma columna no pueden colisionar."""
    assert "column_0_N_name" in NAMING_CONVENTION["ix"]
    assert "column_0_N_name" in NAMING_CONVENTION["uq"]
