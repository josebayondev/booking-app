// Configuración de Vite: qué plugins transforman el código en desarrollo y en el build,
// más la configuración de Vitest, que reutiliza este mismo pipeline.
// Documentación: https://vite.dev/config/
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
// `vitest/config` y no `vite`: es el mismo defineConfig más la clave `test`, que el de
// Vite no conoce.
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    // Los tests de componentes necesitan DOM; los de lógica pura no, pero no compensa
    // partir la configuración en dos por eso.
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // Sin `globals: true`: cada test importa lo que usa. Un poco más de ruido en los
    // imports a cambio de que nada aparezca por arte de magia y de no tener que declarar
    // tipos globales en el tsconfig.
    globals: false,
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
