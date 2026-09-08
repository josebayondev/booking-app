// Los tres pasos hasta la confirmación. Es la sección que sostiene la decisión de no pedir
// registro: quien no sabe qué va a pasar al pulsar el botón, no lo pulsa.
//
// El número de cada paso es tipografía grande y clara en vez de una línea conectora entre
// insignias: da el mismo ritmo de "uno, dos, tres" sin posicionamiento absoluto que se
// pueda descolocar en un ancho raro.
import type { LandingContent } from '../../content/landing.ts'

interface ProcessProps {
  content: LandingContent['process']
}

export default function Process({ content }: ProcessProps) {
  return (
    <section>
      <p className="text-xs font-medium tracking-wide text-stone-500 uppercase">
        {content.eyebrow}
      </p>
      <h2 className="mt-2 text-2xl font-bold tracking-tight text-balance text-stone-900 sm:text-3xl">
        {content.title}
      </h2>

      <ol className="mt-10 grid gap-10 sm:grid-cols-3 sm:gap-8">
        {content.steps.map((step, index) => (
          <li key={step.title}>
            <span
              aria-hidden
              className="block text-4xl font-bold tracking-tight text-stone-300 tabular-nums"
            >
              {String(index + 1).padStart(2, '0')}
            </span>
            <h3 className="mt-3 text-lg font-semibold text-stone-900">
              {step.title}
            </h3>
            <p className="mt-2 max-w-[45ch] text-sm leading-relaxed text-pretty text-stone-600">
              {step.body}
            </p>
          </li>
        ))}
      </ol>
    </section>
  )
}
