// Ruta `/cita/:token`: gestión de una cita ya reservada. Placeholder hasta FEAT 21.
//
// Es la URL a la que apunta el enlace del email de confirmación, así que casi siempre se
// abre en frío, pegada en la barra de direcciones. El acceso va por token opaco y nunca
// por un id secuencial, para que nadie pueda pasearse por las citas ajenas cambiando un
// número.
import { useParams } from 'react-router'

export default function AppointmentPage() {
  // `noUncheckedIndexedAccess` obliga a contar con que no venga; la ruta garantiza que sí,
  // pero el tipo no lo sabe.
  const { token } = useParams<{ token: string }>()

  return (
    <>
      <h2 className="text-2xl font-bold">Tu cita</h2>
      <p>Pendiente de FEAT 21: ver, mover o cancelar la cita de este token.</p>
      <p className="mt-2 font-mono text-sm">token: {token ?? '(ninguno)'}</p>
    </>
  )
}
