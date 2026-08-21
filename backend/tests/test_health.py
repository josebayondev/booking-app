"""Tests del endpoint /health, incluido el HEAD que usan las sondas de uptime."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.db
def test_health_returns_ok(running_client: TestClient) -> None:
    """running_client arranca el lifespan, así que check_db_connection() corre de verdad."""
    response = running_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_answers_head_requests(client: TestClient) -> None:
    """Las sondas de uptime usan HEAD por defecto, y FastAPI no lo añade implícitamente."""
    response = client.head("/health")

    assert response.status_code == 200
