// Componente raíz de la aplicación. Hoy es un placeholder: el andamiaje tiene que poder
// arrancar y compilar, pero las pantallas reales llegan con el flujo de reserva.
import { useUiStore } from './features/ui/uiStore'

export default function App() {
  // Un selector por dato, no `useUiStore()` entero: así el componente solo se vuelve a
  // renderizar cuando cambia lo que de verdad lee.
  const isMobileMenuOpen = useUiStore((state) => state.isMobileMenuOpen)
  const toggleMobileMenu = useUiStore((state) => state.toggleMobileMenu)

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold text-blue-600">AppCitas</h1>
      <p>Reserva de citas. Andamiaje en marcha.</p>

      {/* Ejemplo vivo del store: se sustituye por la navegación real en FEAT 20. */}
      <button
        type="button"
        className="mt-4 rounded border px-3 py-1"
        aria-expanded={isMobileMenuOpen}
        onClick={toggleMobileMenu}
      >
        {isMobileMenuOpen ? 'Cerrar menú' : 'Abrir menú'}
      </button>
    </main>
  )
}
