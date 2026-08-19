import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import Settings

logger = logging.getLogger(__name__)


def configure_sentry(settings: Settings) -> None:
    """Initialise Sentry when a DSN is configured, otherwise do nothing.

    Leaving SENTRY_DSN unset is the normal case locally and in CI, so this is a
    no-op there instead of shipping events from a developer machine.
    """
    if not settings.sentry_dsn:
        logger.info("Sentry disabled: SENTRY_DSN is not set")
        return

    try:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            # This is a public repo and bookings carry personal data: never attach
            # request bodies, headers, cookies or client IP addresses to an event.
            send_default_pii=False,
            integrations=[
                # Breadcrumbs from INFO up, and one Sentry event per logging.error()
                # call. These are the SDK defaults, spelled out so a future change to
                # them cannot silently stop reporting errors.
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
        )
    except Exception:
        # A malformed DSN raises BadDsn, and this runs at import time in main.py,
        # so an unguarded failure kills the container. Losing telemetry is bad;
        # refusing to serve requests because telemetry is misconfigured is worse.
        logger.exception("Sentry init failed, continuing without it")
        return

    logger.info("Sentry enabled for environment %s", settings.environment)
