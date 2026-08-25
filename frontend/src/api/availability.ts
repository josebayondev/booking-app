// GET /api/v1/availability: qué huecos quedan libres en un rango de días.

import { z } from 'zod'

import { request } from './http.ts'

/**
 * Un instante en UTC, convertido a `Date` aquí mismo.
 *
 * Es el borde de la aplicación, que es donde el proyecto convierte tiempo (ver
 * `CLAUDE.md`): de aquí hacia arriba se trabaja con `Date`, nunca con la cadena ISO. El
 * `refine` va después del `transform` porque `new Date('cualquier cosa')` no lanza, se
 * queda en `Invalid Date` y se propaga en silencio hasta pintar "NaN" en pantalla.
 */
const utcInstant = z
  .string()
  .transform((value) => new Date(value))
  .refine((date) => !Number.isNaN(date.getTime()), {
    message: 'no es un instante ISO 8601 válido',
  })

const freeSlotSchema = z
  .object({ starts_at: utcInstant, ends_at: utcInstant })
  .transform((raw) => ({ startsAt: raw.starts_at, endsAt: raw.ends_at }))

/**
 * El día se queda en texto `YYYY-MM-DD` a propósito, sin pasar por `Date`.
 *
 * No es un instante: es la etiqueta del día natural en la zona del dueño
 * (`Europe/Madrid`). Convertirlo a `Date` lo clavaría a medianoche UTC y a un visitante en
 * Canarias o en Argentina le pintaría el día anterior — el fallo de zona horaria que
 * FEAT 21 tiene que evitar, colado ya desde la capa de datos.
 */
const localDaySchema = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'debe ser una fecha YYYY-MM-DD')

export const dayAvailabilitySchema = z.object({
  date: localDaySchema,
  slots: z.array(freeSlotSchema),
})

export type DayAvailability = z.infer<typeof dayAvailabilitySchema>
export type FreeSlot = DayAvailability['slots'][number]

const availabilitySchema = z.array(dayAvailabilitySchema)

/** `from` y `to` son días naturales `YYYY-MM-DD`, no instantes: el backend los proyecta
 * sobre la zona del dueño. El backend rechaza rangos de más de 62 días. */
export type AvailabilityParams = {
  type: string
  from: string
  to: string
}

export function getAvailability(
  params: AvailabilityParams,
): Promise<DayAvailability[]> {
  // Los nombres de los query params son los de la URL pública (`type`, `from`, `to`), que
  // no coinciden con los atributos del schema Pydantic porque `from` es palabra reservada
  // en Python.
  return request('/availability', availabilitySchema, {
    type: params.type,
    from: params.from,
    to: params.to,
  })
}
