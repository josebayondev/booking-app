// Tests del store de estado de cliente de la interfaz.

import { beforeEach, describe, expect, it } from 'vitest'

import { useUiStore } from './uiStore'

describe('useUiStore', () => {
  beforeEach(() => {
    // El store vive a nivel de módulo y sobrevive entre tests: sin este reset, el estado
    // que deja uno decide el resultado del siguiente.
    useUiStore.setState({ isMobileMenuOpen: false })
  })

  it('empieza con el menú cerrado', () => {
    expect(useUiStore.getState().isMobileMenuOpen).toBe(false)
  })

  it('toggleMobileMenu invierte el flag', () => {
    useUiStore.getState().toggleMobileMenu()
    expect(useUiStore.getState().isMobileMenuOpen).toBe(true)

    useUiStore.getState().toggleMobileMenu()
    expect(useUiStore.getState().isMobileMenuOpen).toBe(false)
  })

  it('closeMobileMenu cierra esté como esté', () => {
    useUiStore.getState().toggleMobileMenu()
    useUiStore.getState().closeMobileMenu()
    expect(useUiStore.getState().isMobileMenuOpen).toBe(false)

    // Cerrar lo ya cerrado no lo reabre.
    useUiStore.getState().closeMobileMenu()
    expect(useUiStore.getState().isMobileMenuOpen).toBe(false)
  })
})
