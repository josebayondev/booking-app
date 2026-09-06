"""Contrato de POST /api/v1/admin/login."""

from pydantic import BaseModel, Field


class AdminLoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=200)


class AdminLoginOut(BaseModel):
    """Sin expires_in: el exp ya va dentro del propio JWT (app/core/security.py); el
    frontend lo lee de ahí en vez de duplicar la expiración en dos sitios."""

    access_token: str
