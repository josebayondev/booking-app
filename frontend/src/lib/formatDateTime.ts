// Formateo de fecha/hora para la interfaz de reserva: siempre en la hora local de quien
// mira la pantalla, nunca en la del dueño (Europe/Madrid) -- ese cambio de zona explícito
// es justo el cuidado que pide FEAT 21.
//
// `timeZone` es opcional y solo existe para que los tests sean deterministas sin depender
// de la zona de la máquina que ejecuta la suite; en la aplicación real se deja sin pasar y
// el navegador aplica la zona real del visitante.

export function formatLocalTime(date: Date, timeZone?: string): string {
  return new Intl.DateTimeFormat('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone,
  }).format(date)
}

export function formatLocalDate(date: Date, timeZone?: string): string {
  return new Intl.DateTimeFormat('es-ES', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    timeZone,
  }).format(date)
}

/**
 * Formatea un día natural `YYYY-MM-DD` (el que devuelve `GET /availability`) sin pasarlo
 * por conversión de zona horaria -- no es un instante, es una etiqueta de día, y
 * convertirlo correría el riesgo de pintarlo un día antes o después según el offset de
 * quien mira la pantalla.
 */
export function formatCalendarDay(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number)
  return new Intl.DateTimeFormat('es-ES', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(new Date(year!, month! - 1, day))
}
