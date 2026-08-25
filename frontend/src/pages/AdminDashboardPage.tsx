// Ruta `/admin`: el panel autenticado. Placeholder hasta FEAT 23 y 24.
//
// Todavía no hay nada que proteja esta ruta: la dependencia `require_role` del backend es
// la que manda, y el frontend solo gestionará la visibilidad de la interfaz. El guard de
// navegación llega con FEAT 23, junto al login.
export default function AdminDashboardPage() {
  return (
    <>
      <h2 className="text-2xl font-bold">Panel</h2>
      <p>
        Pendiente de FEAT 23 (layout) y FEAT 24 (dashboards de citas y
        clientes).
      </p>
    </>
  )
}
