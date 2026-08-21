"""La clase Base declarativa y la convención de nombres de índices y restricciones.

De aquí hereda todo modelo del proyecto, y es lo que hace que los nombres que genera
SQLAlchemy y los que acaba teniendo Postgres coincidan.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Nombres deterministas para cada índice y cada restricción. Postgres bautiza por su
# cuenta todo lo que se deje sin nombre, y esos nombres generados no coinciden con los que
# emitiría SQLAlchemy, así que `alembic check` -- el job de CI que compara los modelos
# contra la base de datos -- reporta desviaciones que no existen. Con la convención puesta,
# ambos lados coinciden.
#
# Esto hay que dejarlo cerrado mientras el esquema está todavía vacío: aplicarlo más tarde
# significa renombrar restricciones vivas en producción.
#
# Dos de los patrones son críticos:
#
# - "column_0_N_name" (y no "column_0_name") en ix/uq escribe todas las columnas del
#   índice. Con solo la primera, dos índices compuestos que empiecen por la misma columna
#   generarían el mismo nombre y Postgres rechazaría el segundo.
#
# - "ck" se apoya en constraint_name, lo que obliga a nombrar a mano cada CheckConstraint
#   (name="duration_range"). Y eso es justo lo que se busca: una violación reporta entonces
#   ck_appointment_type_duration_range en vez de un hash opaco. Un CHECK sin nombre falla al
#   generar la migración -- en local, no en producción.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    # Los nombres de tabla van en singular (booking, appointment_type): una fila es una
    # reserva, y la tabla coincide entonces carácter a carácter con su clase mapeada.
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
