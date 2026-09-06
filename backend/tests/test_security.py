"""Tests de las primitivas JWT de app/core/security.py: emisión, verificación y los dos
casos de fallo que importa distinguir (firma inválida vs. token caducado)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.security import create_access_token, decode_access_token

# Repetido a propósito (entropía casi nula): un valor "de pinta real" aquí dispara el
# escaneo de secretos (gitleaks) en cada PR, aunque no sea más que un fixture de test.
SECRET = "x" * 32


def test_create_and_decode_access_token_round_trip() -> None:
    token = create_access_token(secret=SECRET, expires_minutes=60, subject="admin@example.com")

    payload = decode_access_token(token, secret=SECRET)

    assert payload["sub"] == "admin@example.com"
    assert payload["role"] == "admin"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_expired_token_raises_expired_signature_error() -> None:
    issued_in_the_past = datetime.now(UTC) - timedelta(days=2)
    token = create_access_token(
        secret=SECRET, expires_minutes=60, subject="admin@example.com", now=issued_in_the_past
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, secret=SECRET)


def test_decode_token_with_wrong_secret_raises_invalid_token_error() -> None:
    token = create_access_token(secret=SECRET, expires_minutes=60, subject="admin@example.com")

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token, secret="y" * 32)
