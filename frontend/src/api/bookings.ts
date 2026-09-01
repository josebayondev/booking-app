// Ciclo de vida de una reserva: crearla, consultarla, cancelarla y reprogramarla.

import { z } from 'zod'

import { mutate, request } from './http.ts'

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
 * gestión (la página `/cita/:token`, ver `getBooking()` más abajo) y la referencia para
 * citar en voz alta.
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

/**
 * Calcado de `BookingDetailOut` (`backend/app/schemas/booking.py`): la vista completa que
 * pinta `/cita/:token`. `appointmentType` es el slug -- lo que necesita
 * `getAvailability()` para reprogramar --, `appointmentTypeName` es lo que se muestra.
 */
export const bookingDetailSchema = z
  .object({
    token: z.string().min(1),
    reference: z.string().min(1),
    status: z.enum(['confirmed', 'cancelled']),
    starts_at: utcInstant,
    ends_at: utcInstant,
    customer_name: z.string().min(1),
    appointment_type: z.string().min(1),
    appointment_type_name: z.string().min(1),
  })
  .transform((raw) => ({
    token: raw.token,
    reference: raw.reference,
    status: raw.status,
    startsAt: raw.starts_at,
    endsAt: raw.ends_at,
    customerName: raw.customer_name,
    appointmentType: raw.appointment_type,
    appointmentTypeName: raw.appointment_type_name,
  }))

export type BookingDetail = z.infer<typeof bookingDetailSchema>

export function getBooking(token: string): Promise<BookingDetail> {
  return request(`/bookings/${token}`, bookingDetailSchema)
}

export function cancelBooking(token: string): Promise<BookingDetail> {
  return mutate(`/bookings/${token}/cancel`, bookingDetailSchema, {})
}

export function rescheduleBooking(
  token: string,
  startsAt: Date,
): Promise<BookingDetail> {
  return mutate(`/bookings/${token}/reschedule`, bookingDetailSchema, {
    starts_at: startsAt.toISOString(),
  })
}
