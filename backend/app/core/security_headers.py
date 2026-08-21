"""Cabeceras de seguridad que se añaden a todas las respuestas HTTP.

Se registra la última en main.py, lo que la convierte en el middleware más externo:
Starlette inserta cada middleware nuevo al principio de su lista y monta la pila al
revés. Ese orden importa porque CORSMiddleware contesta él mismo las peticiones de
preflight sin llegar nunca al router, así que solo un middleware que quede por fuera
puede ponerles cabeceras a esas respuestas.
"""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Este servicio solo devuelve JSON, así que no necesita permiso para cargar nada.
STRICT_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"

# Swagger UI y ReDoc sí son páginas HTML de verdad que tiran de un CDN. El
# 'unsafe-inline' para scripts es inevitable: el get_swagger_ui_html() de FastAPI emite
# un <script> en línea que arranca SwaggerUIBundle. ReDoc se trae Montserrat y Roboto de
# Google Fonts, inyecta sus estilos en tiempo de ejecución y lanza web workers desde URLs
# blob:. La política laxa se limita a DOCS_PATHS, y esas rutas ya están apagadas en
# producción (ver docs_url=None en main.py).
DOCS_CSP = (
    "default-src 'none'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com; "
    "connect-src 'self'; "
    "worker-src 'self' blob:; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)

# /openapi.json falta a propósito: es JSON, así que se queda con la política estricta.
DOCS_PATHS = frozenset({"/docs", "/docs/oauth2-redirect", "/redoc"})

# Un año. Sin directiva `preload`: el servicio se aloja bajo onrender.com, un dominio que
# no es nuestro y que no debemos enviar a la lista de precarga.
HSTS_VALUE = "max-age=31536000; includeSubDomains"

BASE_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    # La URL de una reserva lleva un token opaco, así que no puede viajar nunca a un
    # tercero dentro de una cabecera Referer.
    "referrer-policy": "no-referrer",
    "permissions-policy": (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
    ),
}


class SecurityHeadersMiddleware:
    """Middleware ASGI puro: solo reescribe el mensaje de inicio de la respuesta.

    Deliberadamente no hereda de BaseHTTPMiddleware, que hace buffering a través de un
    task group de anyio y rompe las respuestas en streaming y las tareas en segundo
    plano, sin ganar nada cuando lo único que hacemos es fijar cuatro cabeceras.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        hsts: bool,
        docs_paths: frozenset[str] = DOCS_PATHS,
    ) -> None:
        self.app = app
        self.hsts = hsts
        self.docs_paths = docs_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        csp = DOCS_CSP if scope["path"] in self.docs_paths else STRICT_CSP

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                # MutableHeaders reemplaza una cabecera existente en vez de añadir una
                # segunda copia, así que estos valores siempre ganan y nunca se duplican.
                headers = MutableHeaders(scope=message)
                for name, value in BASE_HEADERS.items():
                    headers[name] = value
                headers["content-security-policy"] = csp
                if self.hsts:
                    headers["strict-transport-security"] = HSTS_VALUE
            await send(message)

        await self.app(scope, receive, send_with_headers)
