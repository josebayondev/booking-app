// Guard de ruta del panel: solo gestiona visibilidad de interfaz. La barrera real es
// `require_role` en el backend (FEAT 14) -- redirigir aquí no es seguridad.

import { Navigate, Outlet } from 'react-router'

import { isSessionValid, useAuthStore } from './authStore.ts'

export default function RequireAdminSession() {
  const token = useAuthStore((state) => state.token)
  const expiresAt = useAuthStore((state) => state.expiresAt)

  if (!isSessionValid({ token, expiresAt })) {
    return <Navigate to="/admin/login" replace />
  }

  return <Outlet />
}
