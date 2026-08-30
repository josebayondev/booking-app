// Tests de la orquestación del asistente de reserva: selección automática de tipo cuando
// solo hay uno, los huecos del día elegido, y qué pasa al confirmar -- tanto cuando sale
// bien como cuando el hueco ya no está libre (409).

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { AppointmentType } from '../../api/appointmentTypes.ts'
import { getAppointmentTypes } from '../../api/appointmentTypes.ts'
import type { DayAvailability } from '../../api/availability.ts'
import { getAvailability } from '../../api/availability.ts'
import type { Booking } from '../../api/bookings.ts'
import { createBooking } from '../../api/bookings.ts'
import { ApiError } from '../../api/http.ts'
import { useBookingWizard } from './useBookingWizard.ts'

vi.mock('../../api/appointmentTypes.ts', () => ({
  getAppointmentTypes: vi.fn(),
}))
vi.mock('../../api/availability.ts', () => ({
  getAvailability: vi.fn(),
}))
vi.mock('../../api/bookings.ts', () => ({
  createBooking: vi.fn(),
}))

const TYPE: AppointmentType = {
  slug: 'reunion-inicial',
  name: 'Reunión inicial',
  description: null,
  durationMinutes: 30,
}
const OTHER_TYPE: AppointmentType = {
  slug: 'seguimiento',
  name: 'Seguimiento',
  description: null,
  durationMinutes: 15,
}

const SLOT = {
  startsAt: new Date('2026-09-15T09:00:00Z'),
  endsAt: new Date('2026-09-15T09:30:00Z'),
}
const DAYS: DayAvailability[] = [{ date: '2026-09-15', slots: [SLOT] }]

const BOOKING: Booking = {
  token: 'abc123',
  reference: 'RES-001',
  startsAt: SLOT.startsAt,
  endsAt: SLOT.endsAt,
}

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

describe('useBookingWizard', () => {
  it('elige automáticamente el tipo de cita cuando solo hay uno', async () => {
    vi.mocked(getAppointmentTypes).mockResolvedValue([TYPE])
    vi.mocked(getAvailability).mockResolvedValue(DAYS)

    const { result } = renderHook(() => useBookingWizard(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.selectedType).toEqual(TYPE)
    })
  })

  it('no elige ningún tipo automáticamente cuando hay más de uno', async () => {
    vi.mocked(getAppointmentTypes).mockResolvedValue([TYPE, OTHER_TYPE])
    vi.mocked(getAvailability).mockResolvedValue(DAYS)

    const { result } = renderHook(() => useBookingWizard(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.appointmentTypes.isSuccess).toBe(true)
    })
    expect(result.current.selectedType).toBeNull()
  })

  it('expone los huecos del día elegido', async () => {
    vi.mocked(getAppointmentTypes).mockResolvedValue([TYPE])
    vi.mocked(getAvailability).mockResolvedValue(DAYS)

    const { result } = renderHook(() => useBookingWizard(), {
      wrapper: createWrapper(),
    })
    await waitFor(() => {
      expect(result.current.availability.isSuccess).toBe(true)
    })

    act(() => {
      result.current.selectDate('2026-09-15')
    })

    expect(result.current.daySlots).toEqual([SLOT])
  })

  it('al cambiar de día, olvida el hueco que ya no aplica a ese día', async () => {
    vi.mocked(getAppointmentTypes).mockResolvedValue([TYPE])
    vi.mocked(getAvailability).mockResolvedValue(DAYS)

    const { result } = renderHook(() => useBookingWizard(), {
      wrapper: createWrapper(),
    })
    await waitFor(() => {
      expect(result.current.availability.isSuccess).toBe(true)
    })

    act(() => {
      result.current.selectDate('2026-09-15')
      result.current.selectSlot(SLOT)
    })
    expect(result.current.selectedSlot).toEqual(SLOT)

    act(() => {
      result.current.selectDate('2026-09-16')
    })

    expect(result.current.selectedSlot).toBeNull()
  })

  it('confirma la reserva con el tipo y el hueco elegidos', async () => {
    vi.mocked(getAppointmentTypes).mockResolvedValue([TYPE])
    vi.mocked(getAvailability).mockResolvedValue(DAYS)
    vi.mocked(createBooking).mockResolvedValue(BOOKING)

    const { result } = renderHook(() => useBookingWizard(), {
      wrapper: createWrapper(),
    })
    await waitFor(() => {
      expect(result.current.selectedType).toEqual(TYPE)
    })

    act(() => {
      result.current.selectDate('2026-09-15')
      result.current.selectSlot(SLOT)
    })
    act(() => {
      result.current.confirmBooking('Jose', 'jose@example.com')
    })

    await waitFor(() => {
      expect(result.current.creation.isSuccess).toBe(true)
    })
    expect(vi.mocked(createBooking).mock.calls[0]?.[0]).toEqual({
      type: 'reunion-inicial',
      startsAt: SLOT.startsAt,
      customerName: 'Jose',
      customerEmail: 'jose@example.com',
    })
  })

  it('al confirmar sobre un hueco ya no disponible, lo deselecciona', async () => {
    vi.mocked(getAppointmentTypes).mockResolvedValue([TYPE])
    vi.mocked(getAvailability).mockResolvedValue(DAYS)
    vi.mocked(createBooking).mockRejectedValue(
      new ApiError(
        409,
        'slot_unavailable',
        'Ese horario ya no está disponible.',
      ),
    )

    const { result } = renderHook(() => useBookingWizard(), {
      wrapper: createWrapper(),
    })
    await waitFor(() => {
      expect(result.current.selectedType).toEqual(TYPE)
    })

    act(() => {
      result.current.selectDate('2026-09-15')
      result.current.selectSlot(SLOT)
    })
    act(() => {
      result.current.confirmBooking('Jose', 'jose@example.com')
    })

    await waitFor(() => {
      expect(result.current.creation.isError).toBe(true)
    })
    expect(result.current.selectedSlot).toBeNull()
  })
})
