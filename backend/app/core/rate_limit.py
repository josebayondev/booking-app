"""Rate limiting en memoria para los endpoints públicos bajo /api/v1.

La reserva pública no tiene login, así que no hay ninguna credencial que frene a nadie:
el único endpoint de negocio desplegado hoy -- GET /api/v1/availability -- es además el
más caro que tiene el servicio (cuatro consultas, una conexión del pool y hasta sesenta
días de proyección horaria por petición). Sobre el plan gratuito de Render, con CPU
compartida y una sola instancia, un bucle de curl basta para tumbarlo y para quemar las
horas de cómputo de Neon.

Ventana deslizante y un diccionario en memoria, sin Redis: CLAUDE.md lo descarta
explícitamente, y con una única instancia de Render un contador por proceso *es* el
contador global. Si algún día hay más de una instancia, cada una aplicará el límite por su
cuenta y el techo real será el límite por el número de instancias -- suficiente para lo que
esto defiende, que es no caerse, y el momento de replantearlo será ese y no antes.
"""

import math
import time
from collections import deque
from collections.abc import Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

# La misma forma de error que app/core/errors.py: `code` estable en inglés para que el
# frontend y el chatbot (FEAT 17) ramifiquen sin parsear texto, `detail` en español porque
# es lo que acaba viéndose en la interfaz.
RATE_LIMITED_CODE = "rate_limited"
RATE_LIMITED_DETAIL = "Demasiadas peticiones. Espera unos segundos y vuelve a intentarlo."

# Tope de clientes recordados a la vez. Sin él, el propio limitador sería un vector de
# agotamiento de memoria: basta con pedir desde muchas IPs distintas para que el
# diccionario crezca sin fin. Al superarlo se barre de inmediato en vez de esperar al
# barrido periódico.
MAX_TRACKED_CLIENTS = 10_000


def client_key(scope: Scope, *, trust_forwarded_for: bool) -> str:
    """Con qué identidad se contabiliza una petición.

    Detrás de Render el socket remoto es siempre el balanceador, así que sin mirar
    X-Forwarded-For todo el tráfico compartiría un único cubo y el primer visitante
    dejaría fuera a los demás.

    Se toma el **último** elemento de la cabecera, no el primero. Cada proxy añade al final
    la dirección del par del que recibió la petición, así que con un único proxy de
    confianza por delante -- el de Render -- el último elemento es el que ha escrito ese
    proxy, y por tanto la IP real. El primero es el que puede falsificar el cliente: usarlo
    permitiría saltarse el límite entero rotando la cabecera.

    Fuera de un entorno desplegado (`trust_forwarded_for=False`) la cabecera se ignora del
    todo, porque ahí no hay ningún proxy que la escriba y cualquiera podría inventársela.
    """
    if trust_forwarded_for:
        headers: list[tuple[bytes, bytes]] = scope["headers"]
        for name, value in headers:
            if name == b"x-forwarded-for":
                hops = [hop.strip() for hop in value.decode("latin-1").split(",")]
                real = [hop for hop in hops if hop]
                if real:
                    return real[-1]
                break

    # None cuando no hay socket (tests con transporte en memoria, o ASGI sin peer): un
    # cubo compartido es el comportamiento seguro, nunca "sin límite".
    client: tuple[str, int] | None = scope.get("client")
    return client[0] if client else "unknown"


class RateLimitMiddleware:
    """Middleware ASGI puro que limita las peticiones por cliente bajo un prefijo de ruta.

    No hereda de BaseHTTPMiddleware por el mismo motivo que SecurityHeadersMiddleware: ese
    hace buffering a través de un task group de anyio y rompe las respuestas en streaming,
    sin aportar nada cuando lo único que hay que hacer es contar y dejar pasar.

    Se registra **antes** que CORSMiddleware en main.py, o sea por dentro de él, para que
    la respuesta 429 salga con sus cabeceras CORS. Sin eso el navegador la convertiría en
    un error de red opaco y el frontend no podría ni leer el código ni el Retry-After.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        max_requests: int,
        window_seconds: float,
        path_prefix: str = "/api/v1",
        trust_forwarded_for: bool = False,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.path_prefix = path_prefix
        self.trust_forwarded_for = trust_forwarded_for
        # monotonic y no time(): un ajuste del reloj del sistema no puede dejar el límite
        # colgado ni abrirlo de par en par. Inyectable para que los tests avancen el
        # tiempo sin dormir.
        self.clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._last_sweep = clock()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # /health se queda fuera a propósito: está en la raíz, no bajo el prefijo, y las
        # sondas de uptime lo consultan cada pocos segundos desde una IP fija.
        if scope["type"] != "http" or not scope["path"].startswith(self.path_prefix):
            await self.app(scope, receive, send)
            return

        key = client_key(scope, trust_forwarded_for=self.trust_forwarded_for)
        retry_after = self._register(key)

        if retry_after is not None:
            response = JSONResponse(
                status_code=429,
                content={"code": RATE_LIMITED_CODE, "detail": RATE_LIMITED_DETAIL},
                # Hacia arriba: decir "0" invitaría a reintentar de inmediato y a chocar
                # otra vez contra el límite.
                headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _register(self, key: str) -> float | None:
        """Anota una petición. Devuelve None si pasa, o los segundos que faltan si no.

        No hay ningún `await` entre leer y escribir `self._hits`, así que el bucle de
        eventos no puede intercalar otra petición a mitad y no hace falta ningún lock.
        """
        now = self.clock()
        self._maybe_sweep(now)

        hits = self._hits.setdefault(key, deque())
        cutoff = now - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= self.max_requests:
            # Hueco libre cuando la petición más antigua de la ventana salga de ella.
            return self.window_seconds - (now - hits[0])

        hits.append(now)
        return None

    def _maybe_sweep(self, now: float) -> None:
        """Tira los clientes que ya no tienen ninguna petición dentro de la ventana.

        Una petición solo poda su propia entrada, así que sin este barrido el diccionario
        conservaría para siempre a todo el que haya pasado alguna vez.
        """
        if now - self._last_sweep < self.window_seconds and len(self._hits) <= MAX_TRACKED_CLIENTS:
            return

        cutoff = now - self.window_seconds
        for key, hits in list(self._hits.items()):
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                del self._hits[key]

        self._last_sweep = now
