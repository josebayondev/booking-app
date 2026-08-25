// Tests del criterio de reintento por defecto del QueryClient.
//
// Es la regla que evita machacar el backend con un 429 y reintentar un contrato roto que
// no va a arreglarse solo. No la ve nadie hasta que falla en producción, así que conviene
// que la vea un test.

import { describe, expect, it } from 'vitest'

import { queryClient } from './queryClient'

/** El `retry` por defecto, ya narrowed a función: en el tipo de TanStack Query también
 * puede ser un booleano o un número. */
function defaultRetry(): (failureCount: number, error: Error) => boolean {
  const retry = queryClient.getDefaultOptions().queries?.retry
  if (typeof retry !== 'function') {
    throw new Error('El retry por defecto debería ser una función')
  }
  return retry as (failureCount: number, error: Error) => boolean
}

describe('retry por defecto', () => {
  it('no reintenta lo que se declara no reintentable', () => {
    const error = Object.assign(new Error('409'), { retryable: false })
    expect(defaultRetry()(0, error)).toBe(false)
  })

  it('reintenta lo que se declara reintentable, hasta dos veces', () => {
    const error = Object.assign(new Error('503'), { retryable: true })
    expect(defaultRetry()(0, error)).toBe(true)
    expect(defaultRetry()(1, error)).toBe(true)
    expect(defaultRetry()(2, error)).toBe(false)
  })

  it('reintenta un error sin la marca, que es como llega un fallo de red', () => {
    // El TypeError de un fetch que no llegó a salir: sin `retryable`, y justo el caso que
    // el arranque en frío de Render hace habitual.
    expect(defaultRetry()(0, new TypeError('Failed to fetch'))).toBe(true)
  })
})
