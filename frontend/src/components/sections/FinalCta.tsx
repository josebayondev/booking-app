// Cierre de la página: repite la acción principal para quien ha bajado leyéndolo todo y no
// debería tener que volver arriba a buscarla.
//
// Es el único bloque oscuro de la landing, y ese es justo su trabajo: la inversión de tono
// marca el final sin necesidad de meter un color nuevo en la paleta.
import { Link } from 'react-router'

import type { LandingContent } from '../../content/landing.ts'

interface FinalCtaProps {
  content: LandingContent['finalCta']
}

export default function FinalCta({ content }: FinalCtaProps) {
  return (
    <section className="rounded-3xl bg-stone-900 px-6 py-16 text-center sm:px-16 sm:py-20">
      <h2 className="mx-auto max-w-[20ch] text-3xl leading-[1.1] font-bold tracking-[-0.03em] text-balance text-white sm:text-4xl">
        {content.title.map((line) => (
          <span key={line} className="block">
            {line}
          </span>
        ))}
      </h2>

      <p className="mx-auto mt-5 max-w-[50ch] leading-relaxed text-pretty text-stone-400">
        {content.body}
      </p>

      <Link
        to={content.primary.to}
        className="mt-8 inline-flex items-center gap-2 rounded-xl bg-surface px-6 py-3 text-sm font-semibold text-stone-900 transition-[transform,box-shadow] duration-200 ease-[cubic-bezier(.16,1,.3,1)] hover:-translate-y-0.5 hover:shadow-[0_16px_32px_-12px_rgba(0,0,0,.6)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
      >
        {content.primary.label}
        <span aria-hidden>→</span>
      </Link>

      <p className="mt-5 text-xs text-stone-500">{content.note}</p>
    </section>
  )
}
