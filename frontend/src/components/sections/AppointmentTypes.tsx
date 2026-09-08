// Rejilla de lo que se puede reservar. Es la única sección de la landing cuyos datos vienen
// del backend, así que los recibe ya resueltos por props: quien llama al hook es la página,
// no esta sección -- aquí no se toca `api/` ni TanStack Query.
import type { AppointmentType } from '../../api/appointmentTypes.ts'
import type { LandingContent } from '../../content/landing.ts'
import AppointmentTypeCard from '../AppointmentTypeCard.tsx'
import AppointmentTypeCardSkeleton from '../AppointmentTypeCardSkeleton.tsx'

interface AppointmentTypesProps {
  content: LandingContent['appointmentTypes']
  types: AppointmentType[] | undefined
  isLoading: boolean
  isError: boolean
  onRetry: () => void
}

export default function AppointmentTypes({
  content,
  types,
  isLoading,
  isError,
  onRetry,
}: AppointmentTypesProps) {
  const isEmpty = !isLoading && (types === undefined || types.length === 0)

  return (
    <section id="tipos-de-cita" className="scroll-mt-8">
      <h2 className="text-2xl font-bold tracking-tight text-stone-900 sm:text-3xl">
        {content.title}
      </h2>
      <p className="mt-2 max-w-[60ch] text-pretty text-stone-600">
        {content.subtitle}
      </p>

      {isError ? (
        <div className="mt-8 flex flex-col items-start gap-3 rounded-2xl border border-black/8 bg-surface p-6">
          <p className="text-stone-600">{content.errorMessage}</p>
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center rounded-xl border border-black/8 bg-page px-4 py-2 text-sm font-semibold text-stone-700 transition-colors hover:bg-stone-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
          >
            {content.retryLabel}
          </button>
        </div>
      ) : isEmpty ? (
        <p className="mt-8 text-stone-500">{content.emptyMessage}</p>
      ) : (
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading
            ? // Tres esqueletos: es lo que se ve durante el arranque en frío de Render
              // (~40 s), así que tienen que tener la forma de la tarjeta real.
              Array.from({ length: 3 }, (_, index) => (
                <AppointmentTypeCardSkeleton key={index} />
              ))
            : types?.map((type) => (
                <AppointmentTypeCard
                  key={type.slug}
                  type={type}
                  to="/reservar"
                />
              ))}
        </div>
      )}
    </section>
  )
}
