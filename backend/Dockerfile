# Imagen del backend: build en dos etapas -- una instala las dependencias bloqueadas en un
# venv, la otra se queda solo con ese venv y el código, y corre como usuario sin privilegios.

FROM python:3.13-slim@sha256:7ce4b6dfe35e55397b7cda544f8a13f191b7ae28dc5aad71fe664dbc9bc2623f AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.5@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 /uv /bin/uv

WORKDIR /build

# UV_PROJECT_ENVIRONMENT mantiene el venv en /opt/venv para que la etapa runtime no cambie.
# UV_COMPILE_BYTECODE precompila las dependencias, lo que recorta el arranque en frío de Render.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

# --frozen falla si el lock no está en sintonía con pyproject en vez de volver a resolver,
# así que la imagen recibe siempre las versiones exactas commiteadas en uv.lock.
# --no-install-project instala solo dependencias; la etapa runtime copia app/ directamente
# del contexto de build. Los extras (dev) no se instalan por defecto.
RUN uv sync --frozen --no-install-project


FROM python:3.13-slim@sha256:7ce4b6dfe35e55397b7cda544f8a13f191b7ae28dc5aad71fe664dbc9bc2623f AS runtime

RUN groupadd --system appuser \
    && useradd --system --gid appuser --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser app ./app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health')"

USER appuser

# Forma shell a propósito, para que $PORT se expanda: Render inyecta el puerto por entorno.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
