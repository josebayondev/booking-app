// Tests del guard de ruta del panel: sin sesión o con sesión caducada redirige a
// /admin/login; con sesión válida deja pasar al contenido protegido.

import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router'

import { useAuthStore } from './authStore.ts'
import RequireAdminSession from './RequireAdminSession.tsx'

function renderGuarded() {
  return render(
    <MemoryRouter initialEntries={['/admin']}>
      <Routes>
        <Route path="/admin/login" element={<p>Página de login</p>} />
        <Route path="/admin" element={<RequireAdminSession />}>
          <Route index element={<p>Contenido protegido</p>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

describe('RequireAdminSession', () => {
  beforeEach(() => {
    useAuthStore.setState({ token: null, expiresAt: null })
  })

  it('sin sesión redirige a /admin/login', () => {
    renderGuarded()

    expect(screen.getByText('Página de login')).toBeInTheDocument()
    expect(screen.queryByText('Contenido protegido')).not.toBeInTheDocument()
  })

  it('con la sesión caducada redirige a /admin/login', () => {
    useAuthStore.setState({ token: 'algo', expiresAt: Date.now() - 1 })

    renderGuarded()

    expect(screen.getByText('Página de login')).toBeInTheDocument()
  })

  it('con sesión válida renderiza el contenido protegido', () => {
    useAuthStore.setState({ token: 'algo', expiresAt: Date.now() + 60_000 })

    renderGuarded()

    expect(screen.getByText('Contenido protegido')).toBeInTheDocument()
    expect(screen.queryByText('Página de login')).not.toBeInTheDocument()
  })
})
