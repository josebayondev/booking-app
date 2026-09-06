// Store de sesión del panel de administración: el JWT que emite POST /api/v1/admin/login
// y su caducidad, persistidos para sobrevivir a un refresh de página.

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import { setAuthToken } from '../../api/http.ts'

type AuthState = {
  token: string | null
  /** Epoch ms, leído del claim `exp` del propio JWT -- no lo manda el backend por
   * separado, para no duplicar la caducidad en dos sitios que puedan desincronizarse. */
  expiresAt: number | null
  login: (token: string) => void
  logout: () => void
}

/**
 * `persist` contra `localStorage`: sin esto, refrescar la página perdería la sesión aunque
 * el JWT siguiera siendo válido. `onRehydrateStorage` reengancha el token a `api/http.ts`
 * nada más arrancar la app, antes de que ninguna petición lo necesite.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      expiresAt: null,
      login: (token) => {
        setAuthToken(token)
        set({ token, expiresAt: decodeJwtExpiry(token) })
      },
      logout: () => {
        setAuthToken(null)
        set({ token: null, expiresAt: null })
      },
    }),
    {
      name: 'admin-session',
      onRehydrateStorage: () => (state) => {
        setAuthToken(state?.token ?? null)
      },
    },
  ),
)

/** Si hay sesión y no ha caducado. La barrera real es el backend -- esto solo decide qué
 * pinta la interfaz (mostrar el panel o mandar de vuelta al login). */
export function isSessionValid(
  state: Pick<AuthState, 'token' | 'expiresAt'>,
): boolean {
  return (
    state.token !== null &&
    state.expiresAt !== null &&
    state.expiresAt > Date.now()
  )
}

/**
 * Lee el claim `exp` de un JWT sin verificar su firma -- verificarla es cosa del backend,
 * esto es solo para decidir cuándo mostrar el login. Un token corrupto se trata como
 * sesión ya inválida, nunca como un error que lanzar.
 */
export function decodeJwtExpiry(token: string): number | null {
  try {
    const payload = token.split('.')[1]
    if (payload === undefined) return null
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const json: unknown = JSON.parse(atob(base64))
    const exp = (json as { exp?: unknown }).exp
    return typeof exp === 'number' ? exp * 1000 : null
  } catch {
    return null
  }
}
