"""Conversiones entre el reloj de pared local del dueño y UTC.

Todos los instantes de este proyecto se guardan en UTC. El dueño, en cambio, piensa en
hora local de pared: "los lunes de 10:00 a 14:00" tiene que seguir significando las 10:00
en enero y las 10:00 en julio. Guardado como 09:00Z se convertiría en silencio en las
11:00 locales en cuanto entrase el horario de verano.

Por eso las reglas de disponibilidad guardan una hora local naive más un día de la
semana, y la conversión a un instante real ocurre aquí, contra una fecha concreta:
zoneinfo aplica entonces el desfase que estuviese vigente ese día.

Este módulo es el único sitio donde vive esa conversión, así que los casos límite del
cambio de hora -- dos veces al año -- los cubre un solo grupo pequeño de tests en vez de
estar repartidos por todo el código.
"""

from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from app.core.config import get_settings


@lru_cache
def booking_timezone() -> ZoneInfo:
    """La zona horaria del dueño, desde la configuración. Un dueño y un calendario, así
    que es configuración y no una columna.

    Cacheada porque ZoneInfo parsea la base de datos de zonas al construirse y esto se
    llama una vez por cada cálculo de huecos.
    """
    return ZoneInfo(get_settings().booking_timezone)


def utc_now() -> datetime:
    """El reloj, siempre consciente de zona y en UTC.

    Existe para que quien lo necesite pueda recibirlo como argumento y los tests puedan
    sustituirlo por un instante fijo, y para que nadie tire de datetime.utcnow(), que
    devuelve un datetime *naive* y se compara mal contra todos los conscientes de este
    código.
    """
    return datetime.now(UTC)


def local_to_utc(day: date, wall: time, tz: ZoneInfo | None = None) -> datetime:
    """El instante en el que ocurre una hora local de pared en una fecha dada.

    "Las 10:00 del lunes 7, en Madrid" -> el instante UTC correspondiente. Esto es lo que
    convierte una regla de disponibilidad recurrente en un hueco reservable real.

    Las dos patologías del cambio de hora se resuelven de forma determinista con fold=0, y
    están fijadas por tests:

    - Hora ambigua (último domingo de octubre, las 02:30 pasan dos veces): se elige la
      primera pasada.
    - Hora inexistente (último domingo de marzo, las 02:30 no llegan a existir): se lee con
      el desfase vigente antes del salto, así que cae en el instante que localmente son las
      03:30. Lanzar una excepción sería peor -- ningún horario laboral realista toca de
      02:00 a 03:00, y una excepción ahí convertiría una entrada imposible en una caída.
    """
    tz = tz or booking_timezone()
    return datetime.combine(day, wall, tzinfo=tz).astimezone(UTC)


def utc_to_local_date(moment: datetime, tz: ZoneInfo | None = None) -> date:
    """El día natural local al que pertenece un instante.

    Hace falta para agrupar huecos en la interfaz: 2026-09-01T22:30Z ya es día 2 en
    Madrid, y agrupar por la fecha UTC lo archivaría en el día equivocado del calendario.
    """
    tz = tz or booking_timezone()
    return moment.astimezone(tz).date()


def local_day_bounds(day: date, tz: ZoneInfo | None = None) -> tuple[datetime, datetime]:
    """Límites UTC semiabiertos [inicio, fin) de un día natural local.

    Lo que significa de verdad "bloquear el 15 de agosto entero". Se derivan de las dos
    medianoches en vez de sumando 24 horas, porque los días en que cambia la hora un día
    local dura 23 o 25 horas reales.
    """
    tz = tz or booking_timezone()
    start = local_to_utc(day, time.min, tz)
    end = local_to_utc(day + timedelta(days=1), time.min, tz)
    return start, end
