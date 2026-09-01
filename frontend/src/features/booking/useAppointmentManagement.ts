// Orquesta la página `/cita/:token`: consultar la reserva, cancelarla y reprogramarla.
// Vive aquí y no en AppointmentPage.tsx por la misma razón que useBookingWizard: es
// lógica de interacción, no composición (ver la separación de capas en CLAUDE.md).
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import type { FreeSlot } from '../../api/availability.ts'
import {
  cancelBooking,
  getBooking,
  rescheduleBooking,
} from '../../api/bookings.ts'
import { ApiError } from '../../api/http.ts'
import { addDays, toISODateString } from '../../lib/dateRange.ts'
import { useAvailability } from './useAvailability.ts'

// Misma ventana que useBookingWizard (13.1 acota a 62 días; 34 es de sobra).
const RESCHEDULE_WINDOW_DAYS = 34

export function useAppointmentManagement(token: string) {
  const queryClient = useQueryClient()
  const queryKey = ['booking', token]

  const booking = useQuery({
    queryKey,
    queryFn: () => getBooking(token),
  })

  const cancellation = useMutation({
    mutationFn: () => cancelBooking(token),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKey, updated)
    },
  })

  const [isRescheduling, setIsRescheduling] = useState(false)
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [selectedSlot, setSelectedSlot] = useState<FreeSlot | null>(null)

  function selectDate(date: string) {
    setSelectedDate(date)
    setSelectedSlot(null)
  }

  function startReschedule() {
    setIsRescheduling(true)
  }

  // También se llama al cerrar el panel tras reprogramar con éxito: la fecha y el hueco
  // elegidos ya no aplican a la nueva cita.
  function cancelReschedule() {
    setIsRescheduling(false)
    setSelectedDate(null)
    setSelectedSlot(null)
  }

  const today = new Date()
  const from = toISODateString(today)
  const to = toISODateString(addDays(today, RESCHEDULE_WINDOW_DAYS))
  const appointmentType = booking.data?.appointmentType
  const availability = useAvailability(
    isRescheduling && appointmentType !== undefined
      ? { type: appointmentType, from, to }
      : null,
  )
  const daySlots =
    availability.data?.find((day) => day.date === selectedDate)?.slots ?? []

  const reschedule = useMutation({
    mutationFn: (slot: FreeSlot) => rescheduleBooking(token, slot.startsAt),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKey, updated)
      cancelReschedule()
    },
    onError: (error) => {
      // El hueco que se ofreció ya no es libre: no tiene sentido dejarlo seleccionado, y
      // la disponibilidad cacheada está obsoleta (mismo criterio que useBookingWizard).
      if (error instanceof ApiError && error.code === 'slot_unavailable') {
        setSelectedSlot(null)
        void queryClient.invalidateQueries({ queryKey: ['availability'] })
      }
    },
  })

  function confirmReschedule() {
    if (selectedSlot === null) return
    reschedule.mutate(selectedSlot)
  }

  return {
    booking,
    cancellation,
    isRescheduling,
    startReschedule,
    cancelReschedule,
    availability,
    selectedDate,
    selectDate,
    selectedSlot,
    selectSlot: setSelectedSlot,
    daySlots,
    reschedule,
    confirmReschedule,
  }
}
