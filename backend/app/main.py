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
from app.core.errors import register_error_handlers
from app.core.observability import configure_sentry
from app.core.rate_limit import RateLimitMiddleware
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

# Se añade el primero de los tres, o sea el más interno, para que quede por DENTRO de
# CORSMiddleware: así una respuesta 429 sale con sus cabeceras CORS y el navegador deja al
# frontend leer el código y el Retry-After en vez de convertirla en un error de red opaco.
# Como efecto secundario deseable, los preflight -- que CORSMiddleware contesta él mismo
# sin llegar hasta aquí -- no consumen cupo.
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    # Mismo razonamiento que el HSTS de abajo: fuera de local hay un proxy de Render por
    # delante y el socket remoto es siempre el suyo, así que sin leer X-Forwarded-For todo
    # el tráfico caería en un único cubo. En local no hay proxy y la cabecera solo puede
    # venir falsificada.
    trust_forwarded_for=settings.environment != "local",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    # Sin esto el 429 de RateLimitMiddleware sale con Retry-After en la respuesta real,
    # pero invisible para el JS del navegador: CORS solo expone al fetch/XHR las cabeceras
    # listadas aquí, y Retry-After no es una de las seguras por defecto.
    expose_headers=["Retry-After"],
)

# Se añade el último para que envuelva a CORSMiddleware: las respuestas de preflight las
# contesta el propio CORS y si no saldrían sin ninguna cabecera de seguridad. HSTS se
# decide por el entorno y no por el esquema de la petición porque Render termina el TLS y
# habla HTTP plano con el contenedor, y porque mandar HSTS por http://localhost
# envenenaría la caché HSTS del navegador para cualquier otro proyecto local.
app.add_middleware(SecurityHeadersMiddleware, hsts=settings.environment != "local")

register_error_handlers(app)

app.include_router(health_router)
app.include_router(availability_router)
