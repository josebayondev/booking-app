"""Login del panel de administración: un único rol, sin tabla de usuarios (la identidad
vive en Settings, ver app/core/config.py) y sin cookies -- el JWT viaja en el cuerpo de la
respuesta y luego en la cabecera Authorization: Bearer de cada petición protegida.
"""

from typing import Annotated

import bcrypt
from fastapi import APIRouter, Depends

from app.core.auth import require_role
from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.security import create_access_token
from app.schemas.auth import AdminLoginIn, AdminLoginOut

router = APIRouter(prefix="/api/v1")


@router.post("/admin/login", response_model=AdminLoginOut)
def admin_login(
    credentials: AdminLoginIn,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AdminLoginOut:
    # 1. El panel tiene que estar configurado en este entorno.
    if settings.jwt_secret is None:
        raise ApiError(
            500,
            "auth_not_configured",
            "El panel de administración no está configurado en este entorno.",
        )

    # 2. El email tiene que coincidir con el único admin configurado. Mismo mensaje que
    # una contraseña incorrecta -- nunca se distingue "no existe" de "contraseña
    # equivocada" (mismo principio anti-oráculo que el 404 uniforme de get_booking).
    if credentials.email != settings.admin_email:
        raise ApiError(401, "invalid_credentials", "Email o contraseña incorrectos.")

    # 3. Verificar con bcrypt. Un hash ausente o corrupto cae aquí igual que una
    # contraseña equivocada -- fail closed, mismo mensaje, sin caso especial.
    try:
        password_ok = bcrypt.checkpw(
            credentials.password.encode("utf-8"),
            (settings.admin_password_hash or "").encode("utf-8"),
        )
    except ValueError:
        password_ok = False
    if not password_ok:
        raise ApiError(401, "invalid_credentials", "Email o contraseña incorrectos.")

    # 4. Emitir el JWT.
    token = create_access_token(
        secret=settings.jwt_secret,
        expires_minutes=settings.jwt_expires_minutes,
        subject=credentials.email,
    )
    return AdminLoginOut(access_token=token)


@router.get("/admin/me")
def read_admin_identity(_: Annotated[None, Depends(require_role("admin"))]) -> dict[str, str]:
    # Único propósito: ejercitar require_role de punta a punta con una petición HTTP real.
    # Las rutas de negocio del panel (FEAT 24) harán exactamente lo mismo.
    return {"role": "admin"}
