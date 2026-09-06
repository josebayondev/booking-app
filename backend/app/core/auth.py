"""Dependencia require_role: la barrera real del panel de administración.

El frontend solo gestiona la visibilidad de la interfaz -- ocultar un botón no es
seguridad.
"""

from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.security import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


def require_role(role: str) -> Callable[..., None]:
    """Fábrica de dependencias -- hoy solo existe "admin", pero la firma ya admite más
    roles el día que hagan falta, sin tocar ninguna ruta que ya use require_role("admin")."""

    def _require_role(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> None:
        # 1. Sin cabecera Authorization con esquema Bearer.
        if credentials is None:
            raise ApiError(401, "not_authenticated", "Falta el token de acceso.")

        # 2. El servidor tiene que tener secreto configurado -- narrowing para mypy y un
        # error legible en vez de un TypeError si un despliegue olvida JWT_SECRET.
        if settings.jwt_secret is None:
            raise ApiError(
                500,
                "auth_not_configured",
                "El panel de administración no está configurado en este entorno.",
            )

        # 3. Token inválido o caducado -- ExpiredSignatureError primero porque hereda de
        # InvalidTokenError.
        try:
            payload = decode_access_token(credentials.credentials, secret=settings.jwt_secret)
        except jwt.ExpiredSignatureError:
            raise ApiError(
                401, "token_expired", "La sesión ha caducado, inicia sesión de nuevo."
            ) from None
        except jwt.InvalidTokenError:
            raise ApiError(401, "invalid_token", "Token de acceso inválido.") from None

        # 4. El rol tiene que coincidir.
        if payload.get("role") != role:
            raise ApiError(403, "forbidden", "No tienes permiso para acceder a este recurso.")

    return _require_role
