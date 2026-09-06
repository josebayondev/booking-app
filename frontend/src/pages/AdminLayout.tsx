// Layout del panel autenticado: nav propia (sustituye al Header público mientras se está
// dentro de /admin) + botón de cerrar sesión. FEAT 24 y 25 añadirán más enlaces aquí.
import { NavLink, Outlet } from 'react-router'

import { useAuthStore } from '../features/auth/authStore.ts'

export default function AdminLayout() {
  const logout = useAuthStore((state) => state.logout)

  return (
    <div className="flex flex-col gap-6">
      <nav className="flex items-center justify-between border-b border-black/8 pb-4">
        <NavLink
          to="/admin"
          end
          className="text-sm font-semibold text-stone-900"
        >
          Panel
        </NavLink>

        <button
          type="button"
          onClick={logout}
          className="text-xs font-medium text-stone-400 transition-colors hover:text-stone-600"
        >
          Cerrar sesión
        </button>
      </nav>

      <Outlet />
    </div>
  )
}
