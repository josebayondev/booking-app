// Configuración de Vite: qué plugins transforman el código en desarrollo y en el build.
// Documentación: https://vite.dev/config/
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
})
