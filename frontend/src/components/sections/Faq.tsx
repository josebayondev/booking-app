// Preguntas frecuentes en un acordeón de `<details>`: cero JavaScript, accesible de serie y
// desplegable por el navegador aunque el bundle no llegue a cargar.
//
// Composición asimétrica a propósito (5 columnas de título, 7 de contenido): el resto de la
// página está centrada o en rejilla regular, y esto la saca de la plantilla.
import type { LandingContent } from '../../content/landing.ts'

interface FaqProps {
  content: LandingContent['faq']
}

export default function Faq({ content }: FaqProps) {
  return (
    <section className="grid gap-10 lg:grid-cols-12 lg:gap-16">
      <div className="lg:col-span-5">
        <div className="lg:sticky lg:top-32">
          <p className="text-xs font-medium tracking-wide text-stone-500 uppercase">
            {content.eyebrow}
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-balance text-stone-900 sm:text-3xl">
            {content.title}
          </h2>
        </div>
      </div>

      <div className="lg:col-span-7">
        <dl className="border-t border-black/8">
          {content.items.map((item) => (
            <details
              key={item.question}
              className="group border-b border-black/8"
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-6 py-5 font-semibold text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900 [&::-webkit-details-marker]:hidden">
                <dt>{item.question}</dt>
                {/* El "+" gira 45 grados y se convierte en una "x" al abrir. */}
                <span
                  aria-hidden
                  className="shrink-0 text-xl leading-none font-normal text-stone-400 transition-transform duration-300 ease-[cubic-bezier(.16,1,.3,1)] group-open:rotate-45"
                >
                  +
                </span>
              </summary>
              <dd className="max-w-[60ch] pb-5 leading-relaxed text-pretty text-stone-600">
                {item.answer}
              </dd>
            </details>
          ))}
        </dl>
      </div>
    </section>
  )
}
