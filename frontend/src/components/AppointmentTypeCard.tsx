// Tarjeta de presentación pura para un tipo de cita: recibe los datos ya resueltos y
// compone la tarjeta con el halo que sigue al cursor. No sabe de dónde vienen los datos
// ni si vienen de un mock o de `features/appointmentTypes/`.
import type { MouseEvent } from 'react'
import { Link } from 'react-router'

import type { AppointmentType } from '../api/appointmentTypes'

interface AppointmentTypeCardProps {
  type: AppointmentType
  to: string
}

export default function AppointmentTypeCard({
  type,
  to,
}: AppointmentTypeCardProps) {
  function handleMouseMove(event: MouseEvent<HTMLAnchorElement>) {
    const rect = event.currentTarget.getBoundingClientRect()
    event.currentTarget.style.setProperty(
      '--mx',
      `${String(event.clientX - rect.left)}px`,
    )
    event.currentTarget.style.setProperty(
      '--my',
      `${String(event.clientY - rect.top)}px`,
    )
  }

  return (
    <Link
      to={to}
      onMouseMove={handleMouseMove}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-black/8 bg-surface p-6 transition-[transform,box-shadow,border-color] duration-200 ease-[cubic-bezier(.16,1,.3,1)] hover:-translate-y-0.5 hover:border-stone-900/20 hover:shadow-[0_16px_40px_-16px_rgba(0,0,0,.25)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            'radial-gradient(280px circle at var(--mx) var(--my), rgb(23 23 23 / .06), transparent 70%)',
        }}
      />
      <span className="text-xs font-medium tracking-wide text-stone-500 uppercase">
        {type.durationMinutes} min
      </span>
      <h3 className="mt-2 text-lg font-semibold text-stone-900">{type.name}</h3>
      {type.description !== null && (
        <p className="mt-2 line-clamp-3 flex-1 text-sm leading-relaxed text-pretty text-stone-600">
          {type.description}
        </p>
      )}
      <span className="relative mt-6 inline-flex w-fit items-center text-sm font-medium text-stone-900 after:absolute after:inset-x-0 after:-bottom-0.5 after:h-px after:origin-right after:scale-x-0 after:bg-current after:transition-transform after:duration-300 group-hover:after:origin-left group-hover:after:scale-x-100">
        Reservar
      </span>
    </Link>
  )
}
