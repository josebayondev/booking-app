// Componente raíz: la cabecera común y la tabla de rutas. Cada ruta monta una página de
// `pages/`; el contenido real de cada una llega en su propio FEAT.
import { Link, Route, Routes, useLocation } from 'react-router'

import AdminDashboardPage from './pages/AdminDashboardPage.tsx'
import AdminLoginPage from './pages/AdminLoginPage.tsx'
import AppointmentPage from './pages/AppointmentPage.tsx'
import BookingPage from './pages/BookingPage.tsx'
import LandingPage from './pages/LandingPage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'

export default function App() {
  const location = useLocation()

  return (
    <div className="p-6 sm:p-8">
      <header className="mx-auto flex max-w-6xl items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-stone-900 text-sm font-bold text-white">
            JB
          </span>
          <span className="text-xs font-medium tracking-wide text-stone-500 uppercase">
            Fullstack Developer
          </span>
        </Link>

        <Link
          to="/reservar"
          className="inline-flex items-center rounded-xl bg-stone-900 px-4 py-2 text-sm font-semibold text-white transition-[transform,box-shadow] duration-200 ease-[cubic-bezier(.16,1,.3,1)] hover:-translate-y-0.5 hover:shadow-[0_12px_24px_-10px_rgba(0,0,0,.35)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
        >
          Reservar cita
        </Link>
      </header>

      <main className="mx-auto max-w-6xl">
        {/* `key={pathname}` fuerza a React a remontar este div en cada navegación, así
            que la animación de entrada se repite en cada cambio de ruta, no solo en la
            carga inicial. */}
        <div key={location.pathname} className="animate-fade-up">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/reservar" element={<BookingPage />} />
            <Route path="/cita/:token" element={<AppointmentPage />} />
            <Route path="/admin/login" element={<AdminLoginPage />} />
            <Route path="/admin" element={<AdminDashboardPage />} />
            {/* El comodín va el último: sin él, una URL desconocida no pinta nada. */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
