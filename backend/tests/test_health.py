from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_answers_head_requests() -> None:
    """Uptime probes default to HEAD, and FastAPI does not add it implicitly."""
    # No `with`: HEAD needs no database, so skip the lifespan.
    response = TestClient(app).head("/health")

    assert response.status_code == 200
