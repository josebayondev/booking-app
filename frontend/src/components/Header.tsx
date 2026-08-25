// Cabecera común de la aplicación: fija arriba del viewport en todas las páginas -- no se
// pierde al hacer scroll --, con el monograma con el enlace al inicio y el botón
// persistente de "Reservar cita".
import { Link } from 'react-router'

export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-black/8 bg-page/80 px-6 py-6 backdrop-blur-md sm:px-8">
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-stone-900 text-sm font-bold text-white">
            JB
          </span>
          <span className="text-xs font-medium tracking-wide text-stone-500 uppercase">
            Fullstack Developer
          </span>
        </Link>

        <Link
          to="/reservar"
          className="inline-flex items-center rounded-xl bg-stone-900 px-4 py-2 text-sm font-semibold text-white transition-[transform,box-shadow] duration-200 ease-[cubic-bezier(.16,1,.3,1)] hover:-translate-y-0.5 hover:shadow-[0_12px_24px_-10px_rgba(0,0,0,.35)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
        >
          Reservar cita
        </Link>
      </div>
    </header>
  )
}
