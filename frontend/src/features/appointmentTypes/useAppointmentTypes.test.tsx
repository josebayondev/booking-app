// Tests del hook de tipos de cita: que exponga los datos cuando el backend contesta bien,
// y que propague el error cuando no.

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { AppointmentType } from '../../api/appointmentTypes.ts'
import { getAppointmentTypes } from '../../api/appointmentTypes.ts'
import { useAppointmentTypes } from './useAppointmentTypes.ts'

vi.mock('../../api/appointmentTypes.ts', () => ({
  getAppointmentTypes: vi.fn(),
}))

const APPOINTMENT_TYPE: AppointmentType = {
  slug: 'consulta-inicial',
  name: 'Consulta inicial',
  description: 'Primera toma de contacto.',
  durationMinutes: 30,
}

/** Sin reintentos: un test no tiene por qué esperar los mismos backoffs que la app real. */
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

describe('useAppointmentTypes', () => {
  it('expone los tipos de cita cuando el backend contesta bien', async () => {
    vi.mocked(getAppointmentTypes).mockResolvedValue([APPOINTMENT_TYPE])

    const { result } = renderHook(() => useAppointmentTypes(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })
    expect(result.current.data).toEqual([APPOINTMENT_TYPE])
  })

  it('propaga el error cuando la petición falla', async () => {
    vi.mocked(getAppointmentTypes).mockRejectedValue(new Error('falló'))

    const { result } = renderHook(() => useAppointmentTypes(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
  })
})
