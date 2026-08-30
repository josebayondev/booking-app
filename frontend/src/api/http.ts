// Wrapper fino sobre fetch: construye la URL, valida la respuesta contra su schema de Zod
// y traduce cualquier fallo a un error con forma conocida. Todo lo que hable con el
// backend pasa por aquí.

import type { z } from 'zod'

/**
 * Error con la forma que devuelve el backend para las reglas de negocio:
 * `{"code", "detail"}` (ver `app/core/errors.py`). `code` es estable y en inglés, para
 * ramificar sin parsear texto; `detail` va en español y es lo que puede leer una persona.
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly detail: string
  /** Un 4xx no cambia porque insistas; un 5xx puede ser un tropiezo pasajero. */
  readonly retryable: boolean

  constructor(status: number, code: string, detail: string) {
    super(`${String(status)} ${code}: ${detail}`)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.detail = detail
    this.retryable = status >= 500
  }
}

/**
 * El backend contestó, pero con algo que no es lo pactado.
 *
 * Es la razón de ser de esta capa: sin validar, un campo renombrado en el backend viaja
 * sin ruido hasta reventar tres componentes más abajo con un `undefined`. Aquí falla en el
 * borde, diciendo qué endpoint y qué campo.
 */
export class ApiContractError extends Error {
  /** Reintentar no arregla un contrato roto. */
  readonly retryable = false

  constructor(path: string, issues: z.ZodError) {
    super(
      `La respuesta de ${path} no cumple el contrato esperado: ${issues.message}`,
    )
    this.name = 'ApiContractError'
    this.cause = issues
  }
}

/**
 * Se lee en cada petición y no una vez al importar el módulo: así un test puede montar el
 * entorno antes de llamar, sin pelearse con el orden de los imports.
 */
function apiBaseUrl(): string {
  const value: unknown = import.meta.env.VITE_API_BASE_URL
  if (typeof value !== 'string' || value === '') {
    throw new Error(
      'Falta VITE_API_BASE_URL. Copia .env.example a .env y apunta a la API del backend.',
    )
  }
  return value.replace(/\/$/, '')
}

/** Forma del cuerpo de error del backend, comprobada a mano: aquí ya no se puede confiar
 * en un schema, porque justamente estamos en el camino en el que algo ha ido mal. */
function readApiErrorBody(
  body: unknown,
): { code: string; detail: string } | null {
  if (typeof body !== 'object' || body === null) return null
  const { code, detail } = body as { code?: unknown; detail?: unknown }
  if (typeof code !== 'string' || typeof detail !== 'string') return null
  return { code, detail }
}

/**
 * El envío de la petición y la traducción de su respuesta, compartidos entre `request()` y
 * `mutate()`: los dos validan contra el mismo schema y traducen un error igual, solo
 * cambia cómo se construye la petición.
 */
async function send<TSchema extends z.ZodType>(
  url: URL,
  init: RequestInit,
  schema: TSchema,
  path: string,
): Promise<z.infer<TSchema>> {
  const response = await fetch(url, init)

  if (!response.ok) {
    // Un 422 de FastAPI no tiene esta forma (lleva el detalle campo a campo de Pydantic) y
    // un 502 del proxy de Render puede ni siquiera ser JSON: en esos casos el body no se
    // deja leer y se rellena con un código genérico, sin inventarse un `detail` en español.
    const body: unknown = await response.json().catch(() => null)
    const parsed = readApiErrorBody(body)
    throw new ApiError(
      response.status,
      parsed?.code ?? 'unexpected_error',
      parsed?.detail ?? 'Ha ocurrido un error inesperado. Inténtalo de nuevo.',
    )
  }

  const payload: unknown = await response.json()
  const result = schema.safeParse(payload)
  if (!result.success) {
    throw new ApiContractError(path, result.error)
  }
  return result.data
}

/**
 * Hace la petición y devuelve la respuesta ya validada y tipada.
 *
 * Los fallos de red se dejan salir tal cual (el `TypeError` de fetch): no llevan
 * `retryable`, así que el QueryClient los reintenta, que es justo lo que se quiere con el
 * arranque en frío de Render.
 */
export async function request<TSchema extends z.ZodType>(
  path: string,
  schema: TSchema,
  searchParams?: Record<string, string>,
): Promise<z.infer<TSchema>> {
  const url = new URL(`${apiBaseUrl()}/api/v1${path}`)
  if (searchParams !== undefined) {
    for (const [key, value] of Object.entries(searchParams)) {
      url.searchParams.set(key, value)
    }
  }

  return send(url, { headers: { Accept: 'application/json' } }, schema, path)
}

/**
 * Igual que `request()`, pero para las rutas que escriben: manda `body` como JSON por
 * POST. No lleva `searchParams` porque ninguna mutación de esta aplicación los necesita
 * todavía -- YAGNI hasta que haga falta.
 */
export async function mutate<TSchema extends z.ZodType>(
  path: string,
  schema: TSchema,
  body: unknown,
): Promise<z.infer<TSchema>> {
  const url = new URL(`${apiBaseUrl()}/api/v1${path}`)

  return send(
    url,
    {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    },
    schema,
    path,
  )
}
