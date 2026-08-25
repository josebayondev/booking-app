// GET /api/v1/appointment-types: qué se puede reservar.

import { z } from 'zod'

import { request } from './http.ts'

/**
 * Calcado de `AppointmentTypeOut` (`backend/app/schemas/appointment_type.py`), que a
 * propósito no expone la política interna de reservas (buffer, antelación mínima y
 * máxima): quien está eligiendo qué reservar no la necesita.
 *
 * El `transform` a camelCase es el único sitio donde se cruza la frontera de estilos: el
 * backend habla snake_case y de aquí hacia arriba todo es TypeScript idiomático.
 */
export const appointmentTypeSchema = z
  .object({
    slug: z.string().min(1),
    name: z.string().min(1),
    description: z.string().nullable(),
    duration_minutes: z.number().int().positive(),
  })
  .transform((raw) => ({
    slug: raw.slug,
    name: raw.name,
    description: raw.description,
    durationMinutes: raw.duration_minutes,
  }))

/** El tipo sale del schema, no se declara aparte: dos declaraciones de la misma forma
 * acaban desincronizándose. */
export type AppointmentType = z.infer<typeof appointmentTypeSchema>

const appointmentTypesSchema = z.array(appointmentTypeSchema)

export function getAppointmentTypes(): Promise<AppointmentType[]> {
  return request('/appointment-types', appointmentTypesSchema)
}
