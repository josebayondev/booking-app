// Tests del wrapper HTTP: qué sale de aquí cuando el backend contesta bien, cuando
// contesta con un error de negocio y cuando contesta algo que no es lo pactado.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { z } from 'zod'

import { ApiContractError, ApiError, mutate, request } from './http'

const schema = z.object({ slug: z.string() })

/** Deja `fetch` devolviendo esta respuesta, sin tocar la red. */
function stubFetch(body: unknown, status = 200): void {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify(body), {
          status,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    ),
  )
}

beforeEach(() => {
  vi.stubEnv('VITE_API_BASE_URL', 'http://backend.test')
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

describe('request', () => {
  it('devuelve los datos ya validados cuando la respuesta cumple el schema', async () => {
    stubFetch({ slug: 'consulta-inicial' })
    await expect(request('/algo', schema)).resolves.toEqual({
      slug: 'consulta-inicial',
    })
  })

  it('lanza ApiContractError cuando la respuesta no cumple el schema', async () => {
    // Este es el test que justifica haber metido Zod: sin validación, este `slug`
    // numérico viajaría hasta reventar en un componente, lejos de su causa.
    stubFetch({ slug: 42 })
    await expect(request('/algo', schema)).rejects.toBeInstanceOf(
      ApiContractError,
    )
  })

  it('no reintenta un contrato roto', async () => {
    stubFetch({ slug: 42 })
    await expect(request('/algo', schema)).rejects.toMatchObject({
      retryable: false,
    })
  })

  it('traduce el {code, detail} del backend a un ApiError', async () => {
    stubFetch(
      {
        code: 'appointment_type_not_found',
        detail: 'No existe ese tipo de cita.',
      },
      404,
    )

    await expect(request('/algo', schema)).rejects.toMatchObject({
      status: 404,
      code: 'appointment_type_not_found',
      detail: 'No existe ese tipo de cita.',
      // Un 4xx no cambia por insistir.
      retryable: false,
    })
  })

  it('marca los 5xx como reintentables', async () => {
    stubFetch({ code: 'internal_error', detail: 'Vaya.' }, 503)
    await expect(request('/algo', schema)).rejects.toMatchObject({
      retryable: true,
    })
  })

  it('sobrevive a un 422 de FastAPI, que no tiene la forma {code, detail}', async () => {
    // Pydantic devuelve el detalle campo a campo. No hay `code`, y `detail` es una lista,
    // no una cadena: leerlo a lo bruto rompería el manejo del error justo cuando más
    // falta hace.
    stubFetch(
      { detail: [{ loc: ['query', 'from'], msg: 'campo requerido' }] },
      422,
    )

    const error = await request('/algo', schema).catch(
      (caught: unknown) => caught,
    )
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 422,
      code: 'unexpected_error',
      retryable: false,
    })
  })

  it('falla con un mensaje claro si falta VITE_API_BASE_URL', async () => {
    vi.stubEnv('VITE_API_BASE_URL', '')
    stubFetch({ slug: 'x' })
    await expect(request('/algo', schema)).rejects.toThrow(/VITE_API_BASE_URL/)
  })

  it('cuelga la ruta y los query params de la base', async () => {
    stubFetch([])
    await request('/availability', z.array(z.unknown()), {
      type: 'consulta',
      from: '2026-09-01',
    })

    const [url] = vi.mocked(fetch).mock.calls[0] ?? []
    expect(String(url)).toBe(
      'http://backend.test/api/v1/availability?type=consulta&from=2026-09-01',
    )
  })
})

describe('mutate', () => {
  // Lo único que mutate() añade sobre request() es el método, el cuerpo y la cabecera --
  // la validación y la traducción de errores las hace la misma send() interna, ya
  // probada arriba, así que no hace falta repetir esos casos aquí.
  it('manda POST con el cuerpo en JSON y devuelve los datos ya validados', async () => {
    stubFetch({ slug: 'consulta-inicial' }, 201)

    await expect(mutate('/algo', schema, { name: 'Jose' })).resolves.toEqual({
      slug: 'consulta-inicial',
    })

    const [url, init] = vi.mocked(fetch).mock.calls[0] ?? []
    expect(String(url)).toBe('http://backend.test/api/v1/algo')
    expect(init?.method).toBe('POST')
    expect(init?.body).toBe(JSON.stringify({ name: 'Jose' }))
    expect(new Headers(init?.headers).get('Content-Type')).toBe(
      'application/json',
    )
  })
})
