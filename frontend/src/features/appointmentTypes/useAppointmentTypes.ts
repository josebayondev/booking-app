// Hook de TanStack Query sobre GET /api/v1/appointment-types: qué se puede reservar.

import { useQuery } from '@tanstack/react-query'

import { getAppointmentTypes } from '../../api/appointmentTypes.ts'

export function useAppointmentTypes() {
  return useQuery({
    queryKey: ['appointment-types'],
    queryFn: getAppointmentTypes,
  })
}
