// Orquesta el asistente de reserva de FEAT 21: qué tipo de cita, qué día, qué hora y la
// confirmación. Vive aquí y no en BookingPage.tsx porque es lógica de interacción, no
// composición -- la página solo la lee y pinta (ver la separación de capas en CLAUDE.md).
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import type { AppointmentType } from '../../api/appointmentTypes.ts'
import type { FreeSlot } from '../../api/availability.ts'
import { ApiError } from '../../api/http.ts'
import { addDays, toISODateString } from '../../lib/dateRange.ts'
import { useAppointmentTypes } from '../appointmentTypes/useAppointmentTypes.ts'
import { useAvailability } from './useAvailability.ts'
import { useCreateBooking } from './useCreateBooking.ts'

// 13.1 en ClickUp acota el rango de disponibilidad a 62 días; 35 es de sobra para elegir
// hueco sin acercarse a ese tope.
const AVAILABILITY_WINDOW_DAYS = 34

export function useBookingWizard() {
  const appointmentTypes = useAppointmentTypes()
  const [chosenType, setChosenType] = useState<AppointmentType | null>(null)
  // Con un único tipo activo -- el caso de hoy -- no tiene sentido pararse a preguntar:
  // se deriva en cada render, sin un efecto que dispare un segundo renderizado aparte.
  const selectedType =
    chosenType ??
    (appointmentTypes.data?.length === 1 ? appointmentTypes.data[0]! : null)

  const today = new Date()
  const from = toISODateString(today)
  const to = toISODateString(addDays(today, AVAILABILITY_WINDOW_DAYS))

  const availability = useAvailability(
    selectedType === null ? null : { type: selectedType.slug, from, to },
  )

  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [selectedSlot, setSelectedSlot] = useState<FreeSlot | null>(null)

  // El hueco elegido pertenece al día anterior: si se cambia de día, ya no aplica.
  function selectDate(date: string) {
    setSelectedDate(date)
    setSelectedSlot(null)
  }

  const daySlots =
    availability.data?.find((day) => day.date === selectedDate)?.slots ?? []

  const queryClient = useQueryClient()
  const creation = useCreateBooking()

  function confirmBooking(customerName: string, customerEmail: string) {
    if (selectedType === null || selectedSlot === null) return

    creation.mutate(
      {
        type: selectedType.slug,
        startsAt: selectedSlot.startsAt,
        customerName,
        customerEmail,
      },
      {
        onError: (error) => {
          // El hueco que se ofreció ya no es libre: no tiene sentido dejarlo
          // seleccionado, y la disponibilidad cacheada está obsoleta.
          if (error instanceof ApiError && error.code === 'slot_unavailable') {
            setSelectedSlot(null)
            void queryClient.invalidateQueries({ queryKey: ['availability'] })
          }
        },
      },
    )
  }

  return {
    appointmentTypes,
    selectedType,
    selectType: setChosenType,
    availability,
    selectedDate,
    selectDate,
    selectedSlot,
    selectSlot: setSelectedSlot,
    daySlots,
    creation,
    confirmBooking,
  }
}
