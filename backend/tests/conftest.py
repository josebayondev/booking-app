"""Aislamiento del entorno y fixtures compartidos por toda la suite.

Este fichero hace dos cosas: cortar cualquier vía por la que los tests pudieran acabar
hablando con la base de datos o el Sentry de verdad, y ofrecer las fixtures comunes
(sesión transaccional, cliente HTTP con y sin lifespan, entorno limpio).
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# --------------------------------------------------------------------------------------
# Aislamiento del entorno. Este bloque corre cuando pytest carga este conftest, o sea antes
# de que importe ningún tests/test_*.py -- y ese orden es justo el motivo de que exista.
# app/core/db.py y app/main.py llaman a get_settings() en tiempo de import, y lru_cache
# congela el resultado para el resto de la sesión, así que ninguna fixture puede
# corregirlo después. Nada de este módulo puede importar app.* a nivel de módulo; las
# fixtures de abajo lo importan de forma perezosa.
#
# Sin esto, `uv run pytest` lee backend/.env, que apunta a la rama de desarrollo de Neon, y
# los tests de base de datos abren conexiones reales contra ella.
# --------------------------------------------------------------------------------------

os.environ["ENV_FILE"] = ""

# La misma base de datos que sirve el servicio postgres de docker-compose.yml, y la misma a
# la que apuntan los jobs de CI. setdefault en vez de una asignación dura para que gane el
# DATABASE_URL propio de CI, y para que un desarrollador pueda apuntar la suite a otro sitio
# sin editar nada.
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/booking_app"
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

# Fijado en vez de dejarlo en el valor vacío por defecto para que los tests de CORS puedan
# comprobar un preflight aceptado, y no solo uno rechazado. A propósito no es un origen real
# del frontend: nada fuera de la suite debería reconocerlo.
TEST_CORS_ORIGIN = "http://front.test"
os.environ["CORS_ORIGINS"] = TEST_CORS_ORIGIN

# Aquí no vale setdefault: no hay ninguna razón legítima para que la suite llegue al
# proyecto real de Sentry, y un SENTRY_DSN exportado mandaría ruido de tests a producción.
os.environ["SENTRY_DSN"] = ""

SETTINGS_ENV_VARS = (
    "ENVIRONMENT",
    "PROJECT_NAME",
    "CORS_ORIGINS",
    "DATABASE_URL",
    "SENTRY_DSN",
    "BOOKING_TIMEZONE",
)


@contextmanager
def transactional_session() -> Iterator[Session]:
    """Una sesión cuyas escrituras no sobreviven al bloque, para que un test no pueda
    contaminar a otro.

    join_transaction_mode="create_savepoint" es lo que hace que esto se cumpla incluso
    cuando el test llama a commit(): la sesión hace commit contra un savepoint anidado
    dentro de la transacción externa, y deshacer esa transacción lo descarta todo.

    Se expone como context manager y no solo como la fixture db_session para que un test
    pueda verlo desmontarse y comprobar el rollback desde fuera.
    """
    from app.core.db import SessionLocal, engine

    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def _migrated_schema() -> None:
    """Convierte el "se te ha olvidado migrar" en una frase en vez de una página de traza.

    Un test marcado con db que toca una tabla inexistente falla en las profundidades de
    psycopg con UndefinedTable, una vez por test, lo que entierra lo único que importa
    saber. Comprobar por adelantado las tablas de los modelos contra la base de datos lo
    dice una sola vez, y dice además qué hacer al respecto.

    Se compara contra Base.metadata y no contra el historial de revisiones de alembic a
    propósito: lo que estos tests necesitan son las tablas, y eso sigue siendo cierto tanto
    si el esquema está atrasado, como si se revirtió, como si se apuntó a otra base de datos.

    El mensaje nombra el host y la base de datos porque "ejecuta alembic upgrade head" no
    basta por sí solo para actuar: alembic/env.py lee backend/.env, mientras que el bloque
    del principio de este fichero fija la suite contra el Postgres local. Rutinariamente son
    dos bases de datos distintas, así que un `alembic upgrade head` a secas puede migrar la
    rama de Neon y dejar estos tests fallando contra localhost sin pista de que se haya
    movido nada.
    """
    from sqlalchemy import inspect

    from app.core.db import engine
    from app.models import Base

    missing = sorted(set(Base.metadata.tables) - set(inspect(engine).get_table_names()))
    if missing:
        # Solo host y base de datos. La contraseña no se interpola nunca en el mensaje.
        target = f"{engine.url.database} en {engine.url.host}"
        pytest.fail(
            f"A {target} le faltan estas tablas: {', '.join(missing)}. Alembic sigue "
            f"backend/.env, que puede ser otra base de datos, así que migra esta de forma "
            f"explícita:\n"
            f"  DATABASE_URL={TEST_DATABASE_URL} uv run alembic upgrade head",
            pytrace=False,
        )


@pytest.fixture
def db_session(_migrated_schema: None) -> Iterator[Session]:
    """Una sesión sobre tablas realmente vacías. Marca el test con @pytest.mark.db.

    El vaciado no es redundante con el rollback. El rollback deshace lo que escribe el
    *test*; esto deshace lo que ya estaba confirmado antes de que arrancase pytest -- y en
    local eso no es hipotético, porque `python -m app.seed` es algo normal de ejecutar
    contra la base de datos de desarrollo, y confirma once filas.

    Sin esto, usar la aplicación rompe la suite: un test que comprueba `.one()` encuentra la
    fila sembrada junto a la suya, y uno que comprueba una restricción única pasa por el
    motivo equivocado, chocando con datos sembrados en vez de con la fila que él creó. CI
    levanta un Postgres nuevo en cada ejecución y se quedaría en verde todo el rato, que es
    la peor versión del problema.

    Los DELETE corren dentro de la transacción de la fixture, así que las filas confirmadas
    del desarrollador vuelven en cuanto se hace el rollback. Orden invertido por las claves
    ajenas que llegarán con `booking`.
    """
    from app.models import Base

    with transactional_session() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        yield session


@pytest.fixture
def client() -> TestClient:
    """La app real sin su lifespan, así que no se abre ninguna conexión a base de datos.

    TestClient solo ejecuta el lifespan dentro de un bloque `with`, y esta fixture
    deliberadamente no usa ninguno.
    """
    from app.main import app

    return TestClient(app)


@pytest.fixture
def running_client() -> Iterator[TestClient]:
    """La app real con su lifespan, para que check_db_connection() se ejecute de verdad."""
    from app.main import app

    with TestClient(app) as started:
        yield started


@pytest.fixture
def api_client(db_session: Session) -> Iterator[TestClient]:
    """Un TestClient cuyas rutas leen y escriben en la MISMA transacción que db_session.

    Sin esto, un endpoint bajo prueba abriría su propia sesión contra el engine
    (Depends(get_db) crea un SessionLocal() nuevo, sobre otra conexión del pool), que no
    vería nada de lo que un test prepara con db_session -- Postgres no enseña filas no
    confirmadas de una transacción a otra conexión. app.dependency_overrides sustituye
    esa dependencia por una que sencillamente reutiliza la sesión de db_session, así que
    lo que el test inserta ya está ahí para el endpoint, y todo se deshace igual al
    terminar (el rollback de db_session, no un commit de verdad).
    """
    from app.core.db import get_db
    from app.main import app

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        del app.dependency_overrides[get_db]


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Borra todas las variables de Settings, para los tests que comprueban los valores por
    defecto o el .env.example. Sin ella, el bloque de aislamiento de arriba taparía lo que
    esos tests leen."""
    for name in SETTINGS_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
