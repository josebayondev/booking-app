"""Emisión y verificación del JWT de sesión del panel de administración.

HS256, sin cookies -- el token viaja en la cabecera Authorization: Bearer. Todo entra por
parámetro (secreto, minutos, reloj) para que los tests puedan fabricar tokens caducados
sin esperar ni tocar Settings -- mismo criterio que utc_now() en app/core/timezone.py.
"""

from datetime import datetime, timedelta
from typing import Any

import jwt

from app.core.timezone import utc_now


def create_access_token(
    *, secret: str, expires_minutes: int, subject: str, now: datetime | None = None
) -> str:
    issued_at = now or utc_now()
    payload = {
        "sub": subject,
        "role": "admin",
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, *, secret: str) -> dict[str, Any]:
    # algorithms= explícito a propósito: sin él, PyJWT aceptaría cualquier algoritmo que
    # traiga el propio token, que es la confusión de algoritmo que ha dado tantos CVEs a
    # JWT mal usado.
    return jwt.decode(token, secret, algorithms=["HS256"])
