"""Tests del limitador de peticiones: el corte en el límite, la ventana deslizante, de qué
elemento de X-Forwarded-For sale la identidad del cliente y que el diccionario interno no
crece sin fin.

Se montan sobre una app desechable con límites diminutos, no sobre app.main, para que no
dependan de cómo esté cableado main.py ni de la configuración de la suite.
"""

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.core.rate_limit import (
    MAX_TRACKED_CLIENTS,
    RATE_LIMITED_CODE,
    RateLimitMiddleware,
    client_key,
)


class FakeClock:
    """Un reloj que solo avanza cuando el test se lo dice, para no dormir en los tests de
    la ventana deslizante."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


async def _ok(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True})


def build_middleware(
    *,
    max_requests: int = 3,
    window_seconds: float = 60.0,
    trust_forwarded_for: bool = False,
    clock: FakeClock | None = None,
) -> RateLimitMiddleware:
    app = Starlette(routes=[Route("/api/v1/thing", _ok), Route("/health", _ok)])
    return RateLimitMiddleware(
        app,
        max_requests=max_requests,
        window_seconds=window_seconds,
        trust_forwarded_for=trust_forwarded_for,
        clock=clock or FakeClock(),
    )


def build_client(**kwargs: object) -> TestClient:
    return TestClient(build_middleware(**kwargs))  # type: ignore[arg-type]


def test_requests_under_the_limit_pass() -> None:
    client = build_client(max_requests=3)

    for _ in range(3):
        assert client.get("/api/v1/thing").status_code == 200


def test_the_request_over_the_limit_is_rejected() -> None:
    client = build_client(max_requests=3)

    for _ in range(3):
        client.get("/api/v1/thing")

    assert client.get("/api/v1/thing").status_code == 429


def test_the_rejection_uses_the_api_error_shape_and_says_when_to_retry() -> None:
    clock = FakeClock()
    client = build_client(max_requests=1, window_seconds=60.0, clock=clock)

    client.get("/api/v1/thing")
    clock.advance(20.0)
    response = client.get("/api/v1/thing")

    assert response.status_code == 429
    assert response.json()["code"] == RATE_LIMITED_CODE
    assert response.json()["detail"]
    # Cuarenta segundos para que la primera petición salga de la ventana de sesenta.
    assert response.headers["Retry-After"] == "40"


def test_retry_after_is_never_zero() -> None:
    """Decir "0" invitaría a reintentar de inmediato y a volver a chocar contra el límite."""
    clock = FakeClock()
    client = build_client(max_requests=1, window_seconds=60.0, clock=clock)

    client.get("/api/v1/thing")
    clock.advance(59.9)

    assert client.get("/api/v1/thing").headers["Retry-After"] == "1"


def test_the_window_slides_instead_of_resetting_on_a_fixed_boundary() -> None:
    clock = FakeClock()
    client = build_client(max_requests=2, window_seconds=60.0, clock=clock)

    client.get("/api/v1/thing")
    clock.advance(30.0)
    client.get("/api/v1/thing")
    assert client.get("/api/v1/thing").status_code == 429

    # A los 61 segundos la primera ha salido de la ventana y libera exactamente un hueco;
    # la segunda, hecha en el segundo 30, sigue dentro.
    clock.advance(31.0)
    assert client.get("/api/v1/thing").status_code == 200
    assert client.get("/api/v1/thing").status_code == 429


def test_paths_outside_the_prefix_are_never_limited() -> None:
    """/health lo consultan las sondas de uptime cada pocos segundos desde una IP fija."""
    client = build_client(max_requests=1)

    for _ in range(10):
        assert client.get("/health").status_code == 200


def test_each_client_gets_its_own_budget() -> None:
    middleware = build_middleware(max_requests=1, trust_forwarded_for=True)
    client = TestClient(middleware)

    assert client.get("/api/v1/thing", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert client.get("/api/v1/thing", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 429
    assert client.get("/api/v1/thing", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 200


def test_a_spoofed_forwarded_for_cannot_buy_extra_budget() -> None:
    """El proxy añade la IP real AL FINAL, así que lo que el cliente escriba por delante no
    cambia con qué identidad se le contabiliza."""
    middleware = build_middleware(max_requests=1, trust_forwarded_for=True)
    client = TestClient(middleware)

    first = client.get("/api/v1/thing", headers={"X-Forwarded-For": "9.9.9.9, 5.6.7.8"})
    second = client.get("/api/v1/thing", headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"})

    assert first.status_code == 200
    assert second.status_code == 429


def test_forwarded_for_is_ignored_when_it_is_not_trusted() -> None:
    """En local no hay proxy que escriba la cabecera, así que solo puede venir inventada."""
    middleware = build_middleware(max_requests=1, trust_forwarded_for=False)
    client = TestClient(middleware)

    assert client.get("/api/v1/thing", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert client.get("/api/v1/thing", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 429


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (b"1.2.3.4, 5.6.7.8", "5.6.7.8"),
        (b"  1.2.3.4 ,  5.6.7.8  ", "5.6.7.8"),
        (b"5.6.7.8", "5.6.7.8"),
        # Una cabecera vacía o basura cae al socket, nunca a "sin límite".
        (b"", "10.0.0.1"),
        (b" , ", "10.0.0.1"),
    ],
)
def test_client_key_reads_the_last_forwarded_hop(header: bytes, expected: str) -> None:
    scope = {
        "type": "http",
        "headers": [(b"x-forwarded-for", header)],
        "client": ("10.0.0.1", 1234),
    }

    assert client_key(scope, trust_forwarded_for=True) == expected


def test_client_key_falls_back_to_a_shared_bucket_without_a_peer() -> None:
    """Sin socket no hay identidad; compartir cubo es seguro, "sin límite" no lo sería."""
    scope = {"type": "http", "headers": [], "client": None}

    assert client_key(scope, trust_forwarded_for=True) == "unknown"


def test_idle_clients_are_forgotten_so_the_tracker_cannot_grow_forever() -> None:
    clock = FakeClock()
    middleware = build_middleware(max_requests=5, window_seconds=60.0, clock=clock)

    for i in range(50):
        middleware._register(f"client-{i}")
    assert len(middleware._hits) == 50

    # Pasada la ventana, la siguiente petición barre a todo el que ya no tenga nada dentro.
    clock.advance(61.0)
    middleware._register("recien-llegado")

    assert list(middleware._hits) == ["recien-llegado"]


def test_the_sweep_also_triggers_on_the_client_cap() -> None:
    """Muchas IPs distintas dentro de una misma ventana no pueden hacer crecer la memoria
    sin freno: superar el tope fuerza un barrido aunque la ventana no haya expirado."""
    clock = FakeClock()
    middleware = build_middleware(max_requests=5, window_seconds=60.0, clock=clock)

    for i in range(MAX_TRACKED_CLIENTS + 1):
        middleware._register(f"client-{i}")

    # Todas siguen dentro de la ventana, así que el barrido no puede tirar ninguna todavía;
    # lo que se comprueba es que se ha ejecutado y ha dejado el reloj del barrido al día.
    assert middleware._last_sweep == clock.now
