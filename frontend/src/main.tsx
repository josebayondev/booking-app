// Punto de entrada del bundle: monta React sobre el <div id="root"> de index.html.
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App.tsx'
import './index.css'

const rootElement = document.getElementById('root')
if (rootElement === null) {
  // Si esto salta, index.html y este fichero se han desincronizado. Mejor un error claro
  // al arrancar que una pantalla en blanco sin explicación.
  throw new Error('No se encuentra el elemento #root en index.html')
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
