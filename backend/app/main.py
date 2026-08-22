"""Punto de entrada de la API: construye la aplicación FastAPI y la deja lista para servir.

Aquí se monta todo en el orden que importa: Sentry antes de que exista la app, el
lifespan que comprueba la base de datos al arrancar, el CORS con su lista blanca de
orígenes, las cabeceras de seguridad por fuera de todo y, al final, los routers.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.availability import router as availability_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.db import check_db_connection
from app.core.observability import configure_sentry
from app.core.security_headers import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)

settings = get_settings()
is_production = settings.environment == "production"

# Antes de que exista la app, para que también se reporte lo que falle al montarla.
configure_sentry(settings)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    check_db_connection()
    yield


app = FastAPI(
    title=settings.project_name,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Se añade el último para que envuelva a CORSMiddleware: las respuestas de preflight las
# contesta el propio CORS y si no saldrían sin ninguna cabecera de seguridad. HSTS se
# decide por el entorno y no por el esquema de la petición porque Render termina el TLS y
# habla HTTP plano con el contenedor, y porque mandar HSTS por http://localhost
# envenenaría la caché HSTS del navegador para cualquier otro proyecto local.
app.add_middleware(SecurityHeadersMiddleware, hsts=settings.environment != "local")

app.include_router(health_router)
app.include_router(availability_router)
