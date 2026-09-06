// Login del panel de administración: un único rol, sin registro (ver `FEAT 14`).

import { z } from 'zod'

import { mutate } from './http.ts'

/** Calcado de `AdminLoginOut` (`backend/app/schemas/auth.py`). Sin `expiresAt`: el propio
 * JWT lleva el claim `exp`, que lee `authStore.ts` en vez de duplicar la caducidad aquí. */
export const adminLoginSchema = z
  .object({ access_token: z.string().min(1) })
  .transform((raw) => ({ accessToken: raw.access_token }))

export type AdminLogin = z.infer<typeof adminLoginSchema>

export function login(email: string, password: string): Promise<AdminLogin> {
  return mutate('/admin/login', adminLoginSchema, { email, password })
}
