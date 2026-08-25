// Preparación común de la suite de Vitest: se ejecuta una vez antes de cada fichero de
// test.

// Añade los matchers de jest-dom (toBeInTheDocument, toHaveAttribute...) al `expect` de
// Vitest, y de paso sus tipos.
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Sin `globals: true`, Testing Library no engancha su limpieza automática: sin esto, cada
// test dejaría su árbol montado en el documento y el siguiente encontraría dos copias de
// lo que busca.
afterEach(() => {
  cleanup()
})
