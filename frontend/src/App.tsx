// Componente raíz: la cabecera común y la tabla de rutas. Cada ruta monta una página de
// `pages/`; el contenido real de cada una llega en su propio FEAT.
import { useEffect, useRef } from 'react'
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
  const mainRef = useRef<HTMLElement>(null)
  const isFirstRender = useRef(true)

  // El remount de `key={pathname}` (más abajo) le quita el foco a lo que se acaba de
  // pulsar, así que lo devolvemos aquí -- a `main` y no a un enlace o botón concreto,
  // porque no hay uno fijo que tenga sentido en las cinco rutas. `preventScroll` porque
  // enfocar ya arrastra scroll consigo: sin él, un `<main>` que empieza justo debajo de la
  // cabecera empuja la página hacia arriba en cada navegación, y aquí lo hacemos a
  // propósito con un `scrollTo` explícito, no como accidente del foco. Nos saltamos el
  // primer render (carga o recarga de página): ahí el foco/scroll no lo decide esta app,
  // lo decide el navegador -- si alguien recarga a media página, forzar el scroll arriba
  // le tira la posición en la que estaba.
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    window.scrollTo({ top: 0 })
    mainRef.current?.focus({ preventScroll: true })
  }, [location.pathname])

  return (
    <div>
      <Header />

      <main
        ref={mainRef}
        tabIndex={-1}
        className="mx-auto max-w-6xl px-6 pb-6 focus:outline-none sm:px-8 sm:pb-8"
      >
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
