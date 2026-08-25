// Ruta comodín: cualquier URL que no case con ninguna de las anteriores.
//
// No es adorno. Con las rutas en cliente, un token mal copiado del email aterriza aquí, y
// sin esta pantalla se quedaría mirando un layout vacío sin saber qué ha pasado.
import { Link } from 'react-router'

export default function NotFoundPage() {
  return (
    <>
      <h2 className="text-2xl font-bold">Esta página no existe</h2>
      <p>Puede que el enlace esté incompleto o haya caducado.</p>
      <Link className="mt-4 inline-block underline" to="/">
        Volver al inicio
      </Link>
    </>
  )
}
