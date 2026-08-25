// Componente raíz: la cabecera común y la tabla de rutas. Cada ruta monta una página de
// `pages/`; el contenido real de cada una llega en su propio FEAT.
import { Route, Routes, useLocation } from 'react-router'

import AdminDashboardPage from './pages/AdminDashboardPage.tsx'
import AdminLoginPage from './pages/AdminLoginPage.tsx'
import AppointmentPage from './pages/AppointmentPage.tsx'
import BookingPage from './pages/BookingPage.tsx'
import LandingPage from './pages/LandingPage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'
import Header from './components/Header.tsx'

export default function App() {
  const location = useLocation()

  return (
    <div>
      <Header />

      <main className="mx-auto max-w-6xl px-6 pb-6 sm:px-8 sm:pb-8">
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
