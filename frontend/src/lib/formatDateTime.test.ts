// Test del formateo de fecha/hora local: el mismo instante UTC tiene que pintar horas
// distintas según la zona del visitante -- es justo el cuidado que pide FEAT 21 (alguien
// en Canarias o en Argentina no puede leer la hora de Madrid sin darse cuenta).

import { describe, expect, it } from 'vitest'

import {
  formatCalendarDay,
  formatLocalDate,
  formatLocalTime,
} from './formatDateTime'

describe('formatLocalTime', () => {
  it('pinta la misma hora UTC en dos zonas distintas con horas distintas', () => {
    const instant = new Date('2026-09-15T09:00:00Z')

    expect(formatLocalTime(instant, 'Europe/Madrid')).toBe('11:00')
    expect(formatLocalTime(instant, 'America/Argentina/Buenos_Aires')).toBe(
      '06:00',
    )
  })
})

describe('formatLocalDate', () => {
  it('incluye el día de la semana, el día del mes y el mes', () => {
    const instant = new Date('2026-09-15T09:00:00Z')
    expect(formatLocalDate(instant, 'Europe/Madrid')).toBe('mar, 15 sept')
  })
})

describe('formatCalendarDay', () => {
  it('pinta el mismo día natural sin importar la zona horaria del navegador', () => {
    // "2026-09-15" es el día natural del dueño (Europe/Madrid), no un instante: pasarlo
    // por Date con conversión de zona lo clavaría a medianoche UTC y, en una zona con
    // offset negativo, lo pintaría un día antes. Aquí no hay `timeZone` que pasar porque
    // no hay instante que convertir.
    expect(formatCalendarDay('2026-09-15')).toBe('mar, 15 sept')
  })
})
