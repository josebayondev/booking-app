// Componente raíz: la cabecera común y la tabla de rutas. Cada ruta monta una página de
// `pages/`; el contenido real de cada una llega en su propio FEAT.
import { Link, Route, Routes } from 'react-router'

import { useUiStore } from './features/ui/uiStore'
import AdminDashboardPage from './pages/AdminDashboardPage.tsx'
import AdminLoginPage from './pages/AdminLoginPage.tsx'
import AppointmentPage from './pages/AppointmentPage.tsx'
import BookingPage from './pages/BookingPage.tsx'
import LandingPage from './pages/LandingPage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'

export default function App() {
  // Un selector por dato, no `useUiStore()` entero: así el componente solo se vuelve a
  // renderizar cuando cambia lo que de verdad lee.
  const isMobileMenuOpen = useUiStore((state) => state.isMobileMenuOpen)
  const toggleMobileMenu = useUiStore((state) => state.toggleMobileMenu)
  const closeMobileMenu = useUiStore((state) => state.closeMobileMenu)

  return (
    <div className="p-8">
      <header className="mb-8">
        <Link
          className="text-3xl font-bold text-blue-600"
          to="/"
          onClick={closeMobileMenu}
        >
          AppCitas
        </Link>

        <button
          type="button"
          className="ml-4 rounded border px-3 py-1"
          aria-expanded={isMobileMenuOpen}
          onClick={toggleMobileMenu}
        >
          {isMobileMenuOpen ? 'Cerrar menú' : 'Abrir menú'}
        </button>

        {/* Navegación provisional: existe para poder recorrer las rutas antes de que haya
            pantallas. FEAT 20 la sustituye por la de verdad. */}
        {isMobileMenuOpen && (
          <nav className="mt-4 flex gap-4 underline">
            <Link to="/reservar" onClick={closeMobileMenu}>
              Reservar
            </Link>
            <Link to="/admin/login" onClick={closeMobileMenu}>
              Iniciar como admin
            </Link>
          </nav>
        )}
      </header>

      <main>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/reservar" element={<BookingPage />} />
          <Route path="/cita/:token" element={<AppointmentPage />} />
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route path="/admin" element={<AdminDashboardPage />} />
          {/* El comodín va el último: sin él, una URL desconocida no pinta nada. */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  )
}
