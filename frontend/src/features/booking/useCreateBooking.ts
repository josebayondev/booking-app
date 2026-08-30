// Hook de TanStack Query sobre POST /api/v1/bookings: crea la reserva sobre el hueco ya
// visto libre en useAvailability.

import { useMutation } from '@tanstack/react-query'

import { createBooking } from '../../api/bookings.ts'

export function useCreateBooking() {
  return useMutation({
    mutationFn: createBooking,
  })
}
