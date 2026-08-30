// Test de las utilidades de rango de fechas: la ventana que BookingPage pide a
// GET /availability.

import { describe, expect, it } from 'vitest'

import { addDays, toISODateString } from './dateRange'

describe('toISODateString', () => {
  it('rellena con ceros el mes y el día', () => {
    expect(toISODateString(new Date(2026, 0, 5))).toBe('2026-01-05')
  })
})

describe('addDays', () => {
  it('cruza de mes correctamente', () => {
    const result = addDays(new Date(2026, 0, 30), 3)
    expect(toISODateString(result)).toBe('2026-02-02')
  })
})
