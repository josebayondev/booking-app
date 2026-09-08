// Pie común de las rutas públicas: quién hay detrás, por dónde escribir y el enlace al
// repositorio. Igual que la cabecera, no se monta dentro de `/admin`.
//
// Sin enlaces legales todavía: aviso legal, privacidad y cookies llegarán cuando haya
// textos de verdad, y enlazarlos a rutas que no existen es peor que no ponerlos.
import type { SiteContent } from '../content/site.ts'

interface FooterProps {
  content: SiteContent['footer']
}

export default function Footer({ content }: FooterProps) {
  return (
    <footer className="mt-24 border-t border-black/8">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-12 sm:flex-row sm:items-start sm:justify-between sm:px-8">
        <div className="max-w-[45ch]">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-stone-900 text-sm font-bold text-white">
            JB
          </span>
          <p className="mt-4 text-sm leading-relaxed text-pretty text-stone-500">
            {content.description}
          </p>
        </div>

        <div className="flex flex-col items-start gap-3 text-sm">
          <a
            href={`mailto:${content.email}`}
            className="relative font-medium text-stone-700 transition-colors after:absolute after:inset-x-0 after:-bottom-0.5 after:h-px after:origin-right after:scale-x-0 after:bg-current after:transition-transform after:duration-300 hover:text-stone-900 hover:after:origin-left hover:after:scale-x-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
          >
            {content.email}
          </a>
          <a
            href={content.repositoryUrl}
            target="_blank"
            rel="noreferrer"
            className="relative font-medium text-stone-700 transition-colors after:absolute after:inset-x-0 after:-bottom-0.5 after:h-px after:origin-right after:scale-x-0 after:bg-current after:transition-transform after:duration-300 hover:text-stone-900 hover:after:origin-left hover:after:scale-x-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
          >
            Código en GitHub
          </a>
          <p className="mt-2 text-xs text-stone-400">
            © {new Date().getFullYear()} {content.legalName}
          </p>
        </div>
      </div>
    </footer>
  )
}
