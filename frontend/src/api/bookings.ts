// POST /api/v1/bookings: reservar un hueco libre.

import { z } from 'zod'

import { mutate } from './http.ts'

/**
 * Un instante en UTC, convertido a `Date` aquí mismo -- mismo criterio que
 * `api/availability.ts`: es el borde de la aplicación, donde se cruza de cadena ISO a
 * `Date`.
 */
const utcInstant = z
  .string()
  .transform((value) => new Date(value))
  .refine((date) => !Number.isNaN(date.getTime()), {
    message: 'no es un instante ISO 8601 válido',
  })

/**
 * Calcado de `BookingOut` (`backend/app/schemas/booking.py`): el token para el enlace de
 * gestión (todavía sin página real, ver FEAT 21) y la referencia para citar en voz alta.
 */
export const bookingSchema = z
  .object({
    token: z.string().min(1),
    reference: z.string().min(1),
    starts_at: utcInstant,
    ends_at: utcInstant,
  })
  .transform((raw) => ({
    token: raw.token,
    reference: raw.reference,
    startsAt: raw.starts_at,
    endsAt: raw.ends_at,
  }))

export type Booking = z.infer<typeof bookingSchema>

/** Lo que manda el visitante: el hueco exacto que vio libre en `getAvailability`, más
 * quién es. `startsAt` viaja con offset porque así lo exige `BookingCreate` en el backend. */
export type BookingCreateParams = {
  type: string
  startsAt: Date
  customerName: string
  customerEmail: string
}

export function createBooking(params: BookingCreateParams): Promise<Booking> {
  return mutate('/bookings', bookingSchema, {
    type: params.type,
    starts_at: params.startsAt.toISOString(),
    customer_name: params.customerName,
    customer_email: params.customerEmail,
  })
}
