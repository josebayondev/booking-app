"""Integración con Sentry y limpieza de datos personales antes de enviarlos.

Este repositorio es público y las reservas llevan datos personales, así que aquí se
inicializa Sentry con `send_default_pii=False` y, sobre todo, se registra el gancho
`before_send` que recorre cada evento redactando emails, teléfonos y cualquier valor
bajo una clave sensible antes de que salga del proceso.
"""

import logging
import re
from typing import Any, cast

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.types import Event, Hint

from app.core.config import Settings

logger = logging.getLogger(__name__)

REDACTED = "[redacted]"

# Claves cuyo valor se descarta tenga la pinta que tenga. Se busca como subcadena, así
# que "user_email" y "customer_phone" quedan cubiertos. "tel" a secas falta a propósito:
# también redactaría "hotel", que en un sistema de reservas es dato de negocio real.
SENSITIVE_KEY_PATTERN = re.compile(
    r"e?mail|phone|telefono|teléfono|m[oó]vil"
    r"|password|passwd|contrase[nñ]a|secret|token|authorization|api[_-]?key"
    r"|cookie|session|dsn|iban|card_number|credit_card|\bdni\b|\bnif\b|\bnie\b",
    re.IGNORECASE,
)

# El texto libre es la otra mitad del problema: una dirección interpolada en un mensaje
# de log ("booking failed for ana@example.com") no pasa nunca por una clave que podamos
# reconocer, así que hay que barrer también los propios valores.
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# Números españoles: nueve dígitos que empiezan por 6-9, con +34 opcional y separadores
# opcionales. Los anclajes \b impiden que enganche dentro de una tirada más larga de
# dígitos, así que timestamps, ids y contadores de bytes sobreviven. Deliberadamente
# estrecho: un patrón laxo redactaría media traza y dejaría los eventos inservibles.
PHONE_PATTERN = re.compile(r"\b(?:\+34[ .-]?)?[6-9]\d{2}[ .-]?\d{3}[ .-]?\d{3}\b")

# Los eventos están anidados, pero no infinitamente: esto solo protege de que una
# estructura patológica o cíclica convierta un informe en un cuelgue.
MAX_SCRUB_DEPTH = 12


def _scrub_value(value: Any, depth: int = 0) -> Any:
    """Recorre un evento recursivamente, redactando por nombre de clave y por forma del valor."""
    if depth > MAX_SCRUB_DEPTH:
        return REDACTED
    if isinstance(value, dict):
        return {
            key: (
                REDACTED
                if isinstance(key, str) and SENSITIVE_KEY_PATTERN.search(key)
                else _scrub_value(item, depth + 1)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub_value(item, depth + 1) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub_value(item, depth + 1) for item in value)
    if isinstance(value, str):
        return PHONE_PATTERN.sub(REDACTED, EMAIL_PATTERN.sub(REDACTED, value))
    return value


def scrub_event(event: Event, hint: Hint) -> Event | None:
    """Quita los datos personales de un evento justo antes de que salga del proceso.

    send_default_pii=False ya evita que Sentry adjunte cuerpos de petición, cabeceras,
    cookies e IPs de cliente. Lo que no puede cubrir son los datos que le metemos
    nosotros: mensajes de log, textos de excepción y las variables locales que Sentry
    captura de cada frame de la pila. Ahí es donde se escapa de verdad el email o el
    teléfono de un cliente, así que esto barre el evento entero.
    """
    return cast("Event", _scrub_value(event))


def configure_sentry(settings: Settings) -> None:
    """Inicializa Sentry si hay DSN configurado y, si no, no hace nada.

    Dejar SENTRY_DSN sin definir es el caso normal en local y en CI, así que ahí esto es
    un no-op en vez de ponerse a enviar eventos desde la máquina de un desarrollador.
    """
    if not settings.sentry_dsn:
        logger.info("Sentry disabled: SENTRY_DSN is not set")
        return

    try:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            # Este repo es público y las reservas llevan datos personales: nunca adjuntar
            # cuerpos de petición, cabeceras, cookies ni IPs de cliente a un evento.
            send_default_pii=False,
            # send_default_pii solo impide que Sentry recoja PII por su cuenta. No hace
            # nada con la PII que le pasamos nosotros en un log o en una variable local.
            before_send=scrub_event,
            integrations=[
                # Migas de pan desde INFO hacia arriba, y un evento de Sentry por cada
                # llamada a logging.error(). Son los valores por defecto del SDK, escritos
                # explícitamente para que un cambio futuro en ellos no pueda dejar de
                # reportar errores en silencio.
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
        )
    except Exception:
        # Un DSN mal formado lanza BadDsn, y esto corre en tiempo de import desde main.py,
        # así que un fallo sin proteger mata el contenedor. Perder telemetría es malo;
        # negarse a servir peticiones porque la telemetría está mal configurada es peor.
        logger.exception("Sentry init failed, continuing without it")
        return

    logger.info("Sentry enabled for environment %s", settings.environment)
