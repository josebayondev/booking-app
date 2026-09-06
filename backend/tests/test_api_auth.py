"""Tests de las rutas de app/api/auth.py.

No tocan base de datos -- el admin es configuración (app/core/config.py), no una fila --
así que usan `client` en vez de `api_client`, y sobrescriben `get_settings` para poder
probar tanto un panel configurado como uno sin configurar en el mismo run. Sin el override,
get_settings() (cacheada con lru_cache) devolvería siempre la misma instancia congelada al
importar app.main, y ningún test posterior podría variar la configuración de admin.
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import bcrypt
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.security import create_access_token

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "correcta-y-larga"
# Repetido a propósito (entropía casi nula): un valor "de pinta real" aquí dispara el
# escaneo de secretos (gitleaks) en cada PR, aunque no sea más que un fixture de test.
JWT_SECRET = "x" * 32


def _settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "admin_email": ADMIN_EMAIL,
        "admin_password_hash": bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode(),
        "jwt_secret": JWT_SECRET,
        "jwt_expires_minutes": 1440,
    }
    return Settings(**(defaults | overrides))  # type: ignore[arg-type]


@pytest.fixture
def override_settings() -> Iterator[Settings]:
    """Sobrescribe get_settings con una Settings de prueba; el valor por defecto tiene el
    admin configurado, y cada test puede pedir otra llamando a esta fixture indirectamente
    (ver test_login_fails_when_admin_not_configured)."""
    from app.main import app

    settings = _settings()

    app.dependency_overrides[get_settings] = lambda: settings
    try:
        yield settings
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_login_with_correct_credentials_returns_token(
    client: TestClient, override_settings: Settings
) -> None:
    response = client.post(
        "/api/v1/admin/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_is_rejected(
    client: TestClient, override_settings: Settings
) -> None:
    response = client.post(
        "/api/v1/admin/login", json={"email": ADMIN_EMAIL, "password": "incorrecta"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "invalid_credentials",
        "detail": "Email o contraseña incorrectos.",
    }


def test_login_with_unknown_email_gives_the_same_error_as_wrong_password(
    client: TestClient, override_settings: Settings
) -> None:
    """Anti-oráculo: "no existe" y "contraseña incorrecta" no pueden distinguirse desde
    fuera, o la respuesta se convierte en un enumerador de emails válidos."""
    response = client.post(
        "/api/v1/admin/login", json={"email": "otro@example.com", "password": ADMIN_PASSWORD}
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "invalid_credentials",
        "detail": "Email o contraseña incorrectos.",
    }


def test_login_fails_closed_when_admin_not_configured(client: TestClient) -> None:
    from app.main import app

    app.dependency_overrides[get_settings] = lambda: Settings()
    try:
        response = client.post(
            "/api/v1/admin/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 500
    assert response.json()["code"] == "auth_not_configured"


def test_me_without_authorization_header_is_rejected(
    client: TestClient, override_settings: Settings
) -> None:
    response = client.get("/api/v1/admin/me")

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


def test_me_with_garbage_token_is_rejected(client: TestClient, override_settings: Settings) -> None:
    response = client.get("/api/v1/admin/me", headers={"Authorization": "Bearer no-soy-un-jwt"})

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


def test_me_with_expired_token_is_rejected(client: TestClient, override_settings: Settings) -> None:
    expired_token = create_access_token(
        secret=JWT_SECRET,
        expires_minutes=60,
        subject=ADMIN_EMAIL,
        now=datetime.now(UTC) - timedelta(days=2),
    )

    response = client.get("/api/v1/admin/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert response.status_code == 401
    assert response.json()["code"] == "token_expired"


def test_me_with_valid_token_from_login_succeeds(
    client: TestClient, override_settings: Settings
) -> None:
    login_response = client.post(
        "/api/v1/admin/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/v1/admin/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"role": "admin"}
