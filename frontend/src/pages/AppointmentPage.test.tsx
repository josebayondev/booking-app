// Test de la ruta con parámetro: que `/cita/:token` monte su página y lea el token.
//
// Es la URL del enlace del email de confirmación, así que es la que más se abre en frío y
// la que peor se nota si se rompe.

import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, it } from 'vitest'

import AppointmentPage from './AppointmentPage.tsx'

describe('AppointmentPage', () => {
  it('lee el token de la ruta', () => {
    render(
      <MemoryRouter initialEntries={['/cita/abc123token']}>
        <Routes>
          <Route path="/cita/:token" element={<AppointmentPage />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'Tu cita' })).toBeInTheDocument()
    expect(screen.getByText(/abc123token/)).toBeInTheDocument()
  })
})
