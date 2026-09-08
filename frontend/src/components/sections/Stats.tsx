// Banda de tres datos del servicio, entre el hero y el proceso. Es una franja con
// separadores y no tres tarjetas: rompe el ritmo de rejilla del resto de la página y pesa
// menos de lo que pesarían tres cajas más.
import type { LandingContent } from '../../content/landing.ts'

interface StatsProps {
  items: LandingContent['stats']
}

export default function Stats({ items }: StatsProps) {
  return (
    <section className="grid grid-cols-1 gap-8 border-y border-black/8 py-10 sm:grid-cols-3 sm:gap-0 sm:divide-x sm:divide-black/8">
      {items.map((item) => (
        <div key={item.label} className="text-center">
          <p className="text-4xl font-bold tracking-tight text-stone-900 tabular-nums">
            {item.value}
          </p>
          <p className="mt-1 text-sm text-stone-500">{item.label}</p>
        </div>
      ))}
    </section>
  )
}
