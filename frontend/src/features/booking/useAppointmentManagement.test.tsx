// Tests de la orquestación de /cita/:token: cargar la reserva, cancelarla, y el flujo de
// reprogramar -- tanto cuando sale bien como cuando el hueco elegido ya no está libre
// (409), igual que useBookingWizard.test.tsx para el asistente de reserva.

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { DayAvailability } from '../../api/availability.ts'
import { getAvailability } from '../../api/availability.ts'
import type { BookingDetail } from '../../api/bookings.ts'
import {
  cancelBooking,
  getBooking,
  rescheduleBooking,
} from '../../api/bookings.ts'
import { ApiError } from '../../api/http.ts'
import { useAppointmentManagement } from './useAppointmentManagement.ts'

vi.mock('../../api/bookings.ts', () => ({
  getBooking: vi.fn(),
  cancelBooking: vi.fn(),
  rescheduleBooking: vi.fn(),
}))
vi.mock('../../api/availability.ts', () => ({
  getAvailability: vi.fn(),
}))

const TOKEN = 'abc123'

const BOOKING: BookingDetail = {
  token: TOKEN,
  reference: 'BK-001',
  status: 'confirmed',
  startsAt: new Date('2026-09-15T09:00:00Z'),
  endsAt: new Date('2026-09-15T09:30:00Z'),
  customerName: 'Ada Lovelace',
  appointmentType: 'reunion-inicial',
  appointmentTypeName: 'Reunión inicial',
}

const NEW_SLOT = {
  startsAt: new Date('2026-09-16T09:00:00Z'),
  endsAt: new Date('2026-09-16T09:30:00Z'),
}
const DAYS: DayAvailability[] = [{ date: '2026-09-16', slots: [NEW_SLOT] }]

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    )
  }
}

describe('useAppointmentManagement', () => {
  it('carga la reserva por token', async () => {
    vi.mocked(getBooking).mockResolvedValue(BOOKING)

    const { result } = renderHook(() => useAppointmentManagement(TOKEN), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.booking.data).toEqual(BOOKING)
    })
    expect(getBooking).toHaveBeenCalledWith(TOKEN)
  })

  it('al cancelar, actualiza la reserva en caché a cancelada', async () => {
    vi.mocked(getBooking).mockResolvedValue(BOOKING)
    vi.mocked(cancelBooking).mockResolvedValue({
      ...BOOKING,
      status: 'cancelled',
    })

    const { result } = renderHook(() => useAppointmentManagement(TOKEN), {
      wrapper: createWrapper(),
    })
    await waitFor(() => {
      expect(result.current.booking.isSuccess).toBe(true)
    })

    act(() => {
      result.current.cancellation.mutate()
    })

    await waitFor(() => {
      expect(result.current.booking.data?.status).toBe('cancelled')
    })
  })

  it('al reprogramar con éxito, actualiza la reserva y cierra el panel', async () => {
    vi.mocked(getBooking).mockResolvedValue(BOOKING)
    vi.mocked(getAvailability).mockResolvedValue(DAYS)
    const rescheduled = {
      ...BOOKING,
      startsAt: NEW_SLOT.startsAt,
      endsAt: NEW_SLOT.endsAt,
    }
    vi.mocked(rescheduleBooking).mockResolvedValue(rescheduled)

    const { result } = renderHook(() => useAppointmentManagement(TOKEN), {
      wrapper: createWrapper(),
    })
    await waitFor(() => {
      expect(result.current.booking.isSuccess).toBe(true)
    })

    act(() => {
      result.current.startReschedule()
    })
    await waitFor(() => {
      expect(result.current.availability.isSuccess).toBe(true)
    })
    expect(vi.mocked(getAvailability).mock.calls[0]?.[0]).toMatchObject({
      type: 'reunion-inicial',
    })

    act(() => {
      result.current.selectDate('2026-09-16')
      result.current.selectSlot(NEW_SLOT)
    })
    act(() => {
      result.current.confirmReschedule()
    })

    await waitFor(() => {
      expect(result.current.booking.data?.startsAt).toEqual(NEW_SLOT.startsAt)
    })
    expect(rescheduleBooking).toHaveBeenCalledWith(TOKEN, NEW_SLOT.startsAt)
    expect(result.current.isRescheduling).toBe(false)
  })

  it('al reprogramar sobre un hueco ya no disponible, lo deselecciona', async () => {
    vi.mocked(getBooking).mockResolvedValue(BOOKING)
    vi.mocked(getAvailability).mockResolvedValue(DAYS)
    vi.mocked(rescheduleBooking).mockRejectedValue(
      new ApiError(
        409,
        'slot_unavailable',
        'Ese horario ya no está disponible.',
      ),
    )

    const { result } = renderHook(() => useAppointmentManagement(TOKEN), {
      wrapper: createWrapper(),
    })
    await waitFor(() => {
      expect(result.current.booking.isSuccess).toBe(true)
    })

    act(() => {
      result.current.startReschedule()
    })
    await waitFor(() => {
      expect(result.current.availability.isSuccess).toBe(true)
    })

    act(() => {
      result.current.selectDate('2026-09-16')
      result.current.selectSlot(NEW_SLOT)
    })
    act(() => {
      result.current.confirmReschedule()
    })

    await waitFor(() => {
      expect(result.current.reschedule.isError).toBe(true)
    })
    expect(result.current.selectedSlot).toBeNull()
    // El panel sigue abierto: quien reprograma elige otro hueco sin volver a pulsar
    // "Reprogramar".
    expect(result.current.isRescheduling).toBe(true)
  })
})
