// Tests del store de sesión del panel: login/logout, y la lógica de caducidad que decide
// si el guard de ruta (`RequireAdminSession.tsx`) deja pasar o no.

import { beforeEach, describe, expect, it } from 'vitest'

import { decodeJwtExpiry, isSessionValid, useAuthStore } from './authStore'

/** Un JWT válido a nivel de forma (header.payload.firma), sin firmar de verdad -- estos
 * tests nunca verifican la firma, solo leen el claim `exp` del payload. */
function fakeJwt(exp: number): string {
  const base64url = (value: unknown): string =>
    btoa(JSON.stringify(value))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '')

  const header = base64url({ alg: 'HS256', typ: 'JWT' })
  const payload = base64url({ sub: 'admin@example.com', role: 'admin', exp })
  return `${header}.${payload}.firma-no-verificada`
}

describe('useAuthStore', () => {
  beforeEach(() => {
    // El store vive a nivel de módulo y sobrevive entre tests, igual que uiStore.
    useAuthStore.setState({ token: null, expiresAt: null })
  })

  it('empieza sin sesión', () => {
    expect(useAuthStore.getState().token).toBeNull()
    expect(useAuthStore.getState().expiresAt).toBeNull()
  })

  it('login guarda el token y calcula expiresAt del claim exp', () => {
    const expSeconds = Math.floor(Date.now() / 1000) + 3600
    const token = fakeJwt(expSeconds)

    useAuthStore.getState().login(token)

    expect(useAuthStore.getState().token).toBe(token)
    expect(useAuthStore.getState().expiresAt).toBe(expSeconds * 1000)
  })

  it('logout limpia token y expiresAt', () => {
    useAuthStore.getState().login(fakeJwt(Math.floor(Date.now() / 1000) + 3600))

    useAuthStore.getState().logout()

    expect(useAuthStore.getState().token).toBeNull()
    expect(useAuthStore.getState().expiresAt).toBeNull()
  })
})

describe('isSessionValid', () => {
  it('es inválida sin token', () => {
    expect(
      isSessionValid({ token: null, expiresAt: Date.now() + 60_000 }),
    ).toBe(false)
  })

  it('es inválida con expiresAt en el pasado', () => {
    expect(isSessionValid({ token: 'algo', expiresAt: Date.now() - 1 })).toBe(
      false,
    )
  })

  it('es válida con token y expiresAt futuro', () => {
    expect(
      isSessionValid({ token: 'algo', expiresAt: Date.now() + 60_000 }),
    ).toBe(true)
  })
})

describe('decodeJwtExpiry', () => {
  it('lee el claim exp en milisegundos', () => {
    const expSeconds = 1_800_000_000
    expect(decodeJwtExpiry(fakeJwt(expSeconds))).toBe(expSeconds * 1000)
  })

  it('devuelve null con un token corrupto, sin lanzar', () => {
    expect(decodeJwtExpiry('no-soy-un-jwt')).toBeNull()
  })
})
