// Ruta `/`: la landing pública -- quién soy, qué ofrezco y la llamada a reservar.
//
// Los tipos de cita son datos de ejemplo por ahora (MOCK_APPOINTMENT_TYPES): el hook real
// de `features/appointmentTypes/`, que pega a `GET /api/v1/appointment-types`, llega en el
// siguiente paso de este mismo FEAT y sustituye este bloque sin tocar el resto de la
// página -- `isLoadingAppointmentTypes` es exactamente el hueco donde entra
// `query.isLoading`.
import { Link } from 'react-router'

import type { AppointmentType } from '../api/appointmentTypes'
import AppointmentTypeCard from '../components/AppointmentTypeCard'
import AppointmentTypeCardSkeleton from '../components/AppointmentTypeCardSkeleton'
import HeroPhoto from '../components/HeroPhoto'
import { CalendarIcon, ClockIcon, ListIcon } from '../components/icons'

const FEATURES = [
  {
    Icon: CalendarIcon,
    title: 'Reserva directa',
    description: 'Sin registro',
  },
  {
    Icon: ClockIcon,
    title: 'Confirmación al momento',
    description: 'Sin esperar un email',
  },
  {
    Icon: ListIcon,
    title: 'Duración clara',
    description: 'Sin sorpresas',
  },
]

const MOCK_APPOINTMENT_TYPES: AppointmentType[] = [
  {
    slug: 'consulta-inicial',
    name: 'Consulta inicial',
    description:
      'Primera toma de contacto: qué necesitas y cómo puedo ayudarte.',
    durationMinutes: 30,
  },
  {
    slug: 'seguimiento',
    name: 'Seguimiento',
    description: 'Para retomar una conversación ya empezada.',
    durationMinutes: 45,
  },
]

const isLoadingAppointmentTypes = false

export default function LandingPage() {
  return (
    <div className="flex flex-col gap-24">
      <section className="grid items-center gap-16 pt-20 lg:grid-cols-12 lg:gap-8">
        <div className="lg:col-span-7">
          <p className="inline-flex items-center gap-2 rounded-full bg-stone-900/5 px-3 py-1 text-xs font-medium tracking-wide text-stone-600 uppercase">
            <CalendarIcon className="h-3.5 w-3.5" />
            Reserva en menos de un minuto
          </p>
          <h1 className="mt-5 text-4xl font-bold tracking-tight text-balance text-stone-900 sm:text-5xl">
            Reserva una reunión conmigo, sin cuentas ni esperas.
          </h1>
          <p className="mt-6 max-w-[55ch] text-lg leading-relaxed text-pretty text-stone-600">
            Elige el tipo de cita, un hueco libre y confírmalo al momento. Sin
            registrarte, sin ida y vuelta de emails.
          </p>

          <ul className="mt-8 flex flex-col gap-4 sm:flex-row sm:gap-8">
            {FEATURES.map(({ Icon, title, description }) => (
              <li key={title} className="flex items-start gap-2.5">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-stone-900/5 text-stone-700">
                  <Icon className="h-4 w-4" />
                </span>
                <span>
                  <span className="block text-sm font-semibold text-stone-900">
                    {title}
                  </span>
                  <span className="block text-sm text-stone-500">
                    {description}
                  </span>
                </span>
              </li>
            ))}
          </ul>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              to="/reservar"
              className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-6 py-3 text-sm font-semibold text-white transition-[transform,box-shadow] duration-200 ease-[cubic-bezier(.16,1,.3,1)] hover:-translate-y-0.5 hover:shadow-[0_16px_32px_-12px_rgba(0,0,0,.45)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
            >
              Reservar una cita
              <span aria-hidden>→</span>
            </Link>
            <a
              href="#tipos-de-cita"
              className="inline-flex items-center rounded-xl border border-black/8 bg-surface px-6 py-3 text-sm font-semibold text-stone-700 transition-colors hover:bg-stone-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
            >
              Ver tipos de cita
            </a>
          </div>

          <p className="mt-6 inline-flex items-center gap-2 rounded-full bg-surface px-3 py-1.5 text-xs text-stone-500">
            <span
              aria-hidden
              className="h-1.5 w-1.5 rounded-full bg-green-500"
            />
            Disponibilidad esta semana
          </p>
        </div>

        <div className="lg:col-span-5">
          <HeroPhoto src="/jose.webp" alt="Jose Bayon" />
        </div>
      </section>

      <section id="tipos-de-cita" className="scroll-mt-8 pb-24">
        <h2 className="text-2xl font-bold tracking-tight text-stone-900">
          Qué puedes reservar
        </h2>
        <p className="mt-2 max-w-[60ch] text-pretty text-stone-600">
          Cada tipo de cita tiene su propia duración. Elige el que mejor encaje.
        </p>

        {MOCK_APPOINTMENT_TYPES.length === 0 && !isLoadingAppointmentTypes ? (
          <p className="mt-8 text-stone-500">
            Todavía no hay tipos de cita configurados.
          </p>
        ) : (
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {isLoadingAppointmentTypes
              ? Array.from({ length: 3 }, (_, index) => (
                  <AppointmentTypeCardSkeleton key={index} />
                ))
              : MOCK_APPOINTMENT_TYPES.map((type) => (
                  <AppointmentTypeCard
                    key={type.slug}
                    type={type}
                    to="/reservar"
                  />
                ))}
          </div>
        )}
      </section>
    </div>
  )
}
