"""Punto de entrada de Alembic: conecta las migraciones con los modelos de la aplicación.

Reutiliza el engine de app/core/db.py, así que `alembic upgrade head` migra la base de
datos que esté configurada -- y ojo, a diferencia de la suite de tests, aquí sí se lee
backend/.env a propósito. `target_metadata` apunta a Base.metadata, que es lo que hace que
autogenerate vea las tablas (y por lo que todo modelo tiene que estar importado en
app/models/__init__.py).
"""

from logging.config import fileConfig

from alembic import context
from app.core.db import engine
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Modo offline: genera el SQL sin conectarse, a partir de la URL configurada."""
    context.configure(
        url=engine.url.render_as_string(hide_password=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo normal: abre una conexión real y aplica las migraciones contra ella."""
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
