// Hook de TanStack Query sobre GET /api/v1/availability: qué días y huecos hay libres
// para un tipo de cita en un rango de fechas.

import { useQuery } from '@tanstack/react-query'

import type { AvailabilityParams } from '../../api/availability.ts'
import { getAvailability } from '../../api/availability.ts'

/** `null` mientras el asistente de reserva todavía no ha elegido tipo de cita: sin tipo
 * no hay nada que pedir, y `enabled: false` evita la petición hasta que lo haya. */
export function useAvailability(params: AvailabilityParams | null) {
  return useQuery({
    queryKey: ['availability', params?.type, params?.from, params?.to],
    queryFn: () => getAvailability(params as AvailabilityParams),
    enabled: params !== null,
  })
}
