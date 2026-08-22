"""Forma de error única de la API pública: `{"code": ..., "detail": ...}`.

`code` es estable y en inglés -- lo que el frontend y, más adelante, el chatbot (FEAT 17)
usan para ramificar sin tener que parsear el texto. `detail` va en español: es lo que
llega a la interfaz. Solo cubre errores de regla de negocio (un tipo de cita que no
existe, un hueco que ya no está libre) -- los 422 de forma de la petición se quedan con
el formato nativo de FastAPI/Pydantic, que ya reporta campo a campo.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Se lanza desde un router; el exception_handler de abajo la traduce a JSON."""

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        self.status_code = status_code
        self.code = code
        self.detail = detail


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content={"code": exc.code, "detail": exc.detail}
        )
