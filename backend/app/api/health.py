"""Endpoint de salud del servicio, usado por las sondas de uptime y por Render."""

from fastapi import APIRouter

router = APIRouter()


# El APIRoute de FastAPI, al contrario que el Route de Starlette, no añade HEAD a una
# ruta GET, así que hay que declararlo a mano. Las sondas de uptime usan HEAD por
# defecto y si no verían un 405 y darían el servicio por caído.
@router.api_route("/health", methods=["GET", "HEAD"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
