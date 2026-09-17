"""Política de retención: borra las reservas pasadas que ya cumplieron su plazo.

`Booking` guarda datos personales (`customer_name`, `customer_email`) sin que quien
reserva tenga cuenta ni control directo sobre ellos -- la reserva pública no tiene login
(ver CLAUDE.md). Minimizar cuánto tiempo sobreviven esos datos es la contrapartida: una
reserva deja de tener uso operativo en cuanto pasa (o se cancela) y el plazo de abajo
termina.

RETENTION_DAYS son 365 días desde `ends_at`, contados independientemente del `status`
(confirmada o cancelada): da un año de historial para lo que necesite FEAT 15 (métricas
del panel) sin retener datos personales indefinidamente. Una vez borrada, una reserva no
es recuperable más que dentro de la ventana de point-in-time recovery de Neon
(`history_retention_seconds = 21600`, es decir 6 horas) -- pasado ese margen, el borrado es
definitivo.

Se ejecuta con `uv run python -m app.cleanup`. Es seguro repetirlo: cada pasada borra
solo lo que en ese momento ya ha cumplido el plazo.
"""

import logging
from datetime import datetime, timedelta
from typing import cast

from sqlalchemy import delete
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from app.core.timezone import utc_now
from app.models import Booking

logger = logging.getLogger(__name__)

RETENTION_DAYS = 365


def delete_past_bookings(session: Session, now: datetime | None = None) -> int:
    """Borra las reservas cuyo `ends_at` quedó a más de RETENTION_DAYS de `now`.

    Recibe `now` por parámetro -- igual que compute_free_slots en
    app/services/availability.py -- para que los tests no dependan del reloj real. No
    hace commit: decide quien llama, igual que seed_defaults().
    """
    now = now or utc_now()
    cutoff = now - timedelta(days=RETENTION_DAYS)

    # session.execute() está tipado como Result[Any] porque cubre también las consultas
    # ORM; para un delete() de Core es en realidad un CursorResult, que es lo único que
    # expone rowcount -- mismo cast que usa la propia SQLAlchemy internamente.
    statement = delete(Booking).where(Booking.ends_at < cutoff)
    result = cast("CursorResult[int]", session.execute(statement))
    return result.rowcount


def main() -> None:
    # Importado aquí y no a nivel de módulo, igual que en app/seed.py: importar
    # app.cleanup no debe construir un engine como efecto colateral.
    from app.core.db import SessionLocal

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with SessionLocal() as session:
        deleted = delete_past_bookings(session)
        session.commit()

    logger.info("Cleanup complete: %d booking(s) deleted past the retention window.", deleted)


if __name__ == "__main__":
    main()
