// Store de Zustand con el estado de cliente de la interfaz: lo que el usuario tiene
// abierto o desplegado en esta pestaña y no existe en el backend.

import { create } from 'zustand'

/**
 * Estado de cliente de la interfaz.
 *
 * Aquí no entra nunca nada que venga de la API: los datos del servidor viven en TanStack
 * Query y duplicarlos en un store es lo que hace que se queden obsoletos sin que nadie se
 * entere. Zustand es solo para lo que decide el usuario mientras navega — un menú
 * desplegado, un filtro elegido, el paso del asistente de reserva cuando llegue.
 */
type UiState = {
  /** Si el menú de navegación de pantallas estrechas está desplegado. */
  isMobileMenuOpen: boolean
  toggleMobileMenu: () => void
  closeMobileMenu: () => void
}

/**
 * De momento es un store de ejemplo: monta el patrón para que las áreas reales (FEAT 20 y
 * 21) lo copien, no cubre todavía ninguna necesidad de producto.
 *
 * `create<UiState>()(...)` va currificado a propósito — es la forma que TypeScript sabe
 * inferir cuando más adelante haya que envolver el store en un middleware (`persist`,
 * `devtools`); la forma directa se rompe en ese momento.
 */
export const useUiStore = create<UiState>()((set) => ({
  isMobileMenuOpen: false,
  toggleMobileMenu: () => {
    set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen }))
  },
  closeMobileMenu: () => {
    set({ isMobileMenuOpen: false })
  },
}))
