import logging

import psycopg

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def check_db_connection() -> None:
    settings = get_settings()
    with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
        conn.execute("SELECT 1")
    logger.info("Database connection OK")
