// Apertura de la landing: el titular, la promesa y la llamada a reservar. Todo el texto
// entra por props desde `content/landing.ts`; aquí no hay ni una frase escrita.
import { Link } from 'react-router'

import type { IconName, LandingContent } from '../../content/landing.ts'
import { CalendarIcon, CheckIcon, ClockIcon, ListIcon } from '../icons.tsx'

// El contenido nombra su icono y aquí se resuelve al componente, para que `content/` siga
// siendo dato serializable en vez de un módulo que importa JSX.
const ICONS: Record<IconName, typeof CalendarIcon> = {
  calendar: CalendarIcon,
  clock: ClockIcon,
  check: CheckIcon,
  list: ListIcon,
}

interface HeroProps {
  content: LandingContent['hero']
}

export default function Hero({ content }: HeroProps) {
  return (
    <section className="mx-auto max-w-4xl pt-16 text-center sm:pt-24">
      <p className="inline-flex items-center gap-2 rounded-full bg-stone-900/5 px-3 py-1 text-xs font-medium tracking-wide text-stone-600 uppercase">
        <CalendarIcon className="h-3.5 w-3.5" />
        {content.eyebrow}
      </p>

      {/* El titular se parte por donde dice el contenido, no por donde caiga el ancho del
          viewport: `title` es un array de líneas. */}
      <h1 className="mt-6 text-4xl leading-[1.05] font-bold tracking-[-0.03em] text-balance text-stone-900 sm:text-5xl">
        {content.title.map((line) => (
          <span key={line} className="block">
            {line}
          </span>
        ))}
      </h1>

      <p className="mx-auto mt-6 max-w-[55ch] text-lg leading-relaxed text-pretty text-stone-600">
        {content.subtitle}
      </p>

      {/* En móvil los tres comparten borde izquierdo (`w-fit` + `items-start`) y el bloque
          entero se centra: con `items-center` cada uno se centraba por su cuenta y los
          iconos quedaban escalonados. */}
      <ul className="mx-auto mt-10 flex w-fit flex-col items-start gap-4 sm:w-auto sm:flex-row sm:justify-center sm:gap-8">
        {content.bullets.map((bullet) => {
          const Icon = ICONS[bullet.icon]
          return (
            <li
              key={bullet.title}
              className="flex items-start gap-2.5 text-left"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-stone-900/5 text-stone-700">
                <Icon className="h-4 w-4" />
              </span>
              <span>
                <span className="block text-sm font-semibold text-stone-900">
                  {bullet.title}
                </span>
                <span className="block text-sm text-stone-500">
                  {bullet.description}
                </span>
              </span>
            </li>
          )
        })}
      </ul>

      <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
        <Link
          to={content.primary.to}
          className="inline-flex items-center gap-2 rounded-xl bg-stone-900 px-6 py-3 text-sm font-semibold text-white transition-[transform,box-shadow] duration-200 ease-[cubic-bezier(.16,1,.3,1)] hover:-translate-y-0.5 hover:shadow-[0_16px_32px_-12px_rgba(0,0,0,.45)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
        >
          {content.primary.label}
          <span aria-hidden>→</span>
        </Link>
        <a
          href={content.secondary.href}
          className="inline-flex items-center rounded-xl border border-black/8 bg-surface px-6 py-3 text-sm font-semibold text-stone-700 transition-colors hover:bg-stone-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
        >
          {content.secondary.label}
        </a>
      </div>

      <p className="mt-6 inline-flex items-center gap-2 rounded-full bg-surface px-3 py-1.5 text-xs text-stone-500">
        <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-green-500" />
        {content.note}
      </p>
    </section>
  )
}
