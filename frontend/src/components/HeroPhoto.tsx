// El retrato del hero: una foto recortada (fondo transparente) flotando sobre un fondo
// decorativo, con un par de chips flotantes a juego con la marca. Sin `src`, muestra un
// hueco de sustitución para que el diseño se vea completo antes de tener el recorte.
import { CalendarIcon, CheckIcon } from './icons'

interface HeroPhotoProps {
  src?: string
  alt: string
}

export default function HeroPhoto({ src, alt }: HeroPhotoProps) {
  return (
    <div className="relative mx-auto flex h-88 w-64 items-end justify-center sm:h-104 sm:w-72">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 opacity-70 blur-[50px]"
        style={{
          background:
            'radial-gradient(at 35% 25%, rgb(23 23 23 / .12) 0px, transparent 55%)',
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-6 -right-8 -z-10 h-24 w-24 text-stone-300 opacity-60 bg-[radial-gradient(currentColor_1px,transparent_1px)] bg-size-[10px_10px]"
      />

      {/* Ventana de código de fondo: puro decorado, ligado a la marca de "desarrollador",
          no a una captura real. */}
      <div
        aria-hidden
        className="pointer-events-none absolute top-24 -left-10 -z-10 w-52 rounded-2xl border border-black/4 bg-surface/30 p-4 font-mono text-[11px] leading-relaxed text-stone-400/50 opacity-70 blur-[0.5px] sm:-left-14 sm:w-60"
      >
        <div className="mb-3 flex gap-1.5">
          <span className="h-2 w-2 rounded-full bg-stone-300/50" />
          <span className="h-2 w-2 rounded-full bg-stone-300/50" />
          <span className="h-2 w-2 rounded-full bg-stone-300/50" />
        </div>
        <pre className="whitespace-pre">{`function App() {
  return (
    <Routes>
      <Route path="/" />
      <Route path="/reservar" />
    </Routes>
  )
}`}</pre>
      </div>

      {src !== undefined ? (
        <img
          src={src}
          alt={alt}
          className="h-full w-full object-contain object-bottom drop-shadow-[0_20px_36px_rgba(0,0,0,.18)]"
        />
      ) : (
        <div className="flex h-full w-full flex-col items-center justify-center gap-1 rounded-3xl border border-dashed border-stone-300 p-4 text-center text-xs text-stone-400">
          <span>Foto recortada</span>
          <span className="text-stone-300">(PNG, fondo transparente)</span>
        </div>
      )}

      <div className="absolute top-6 -left-5 flex h-10 w-10 items-center justify-center rounded-xl border border-black/8 bg-surface text-stone-700 shadow-[0_8px_20px_-8px_rgba(0,0,0,.25)]">
        <CalendarIcon className="h-4 w-4" />
      </div>
      <div className="absolute bottom-16 -right-5 flex h-10 w-10 items-center justify-center rounded-xl border border-black/8 bg-surface text-green-600 shadow-[0_8px_20px_-8px_rgba(0,0,0,.25)]">
        <CheckIcon className="h-4 w-4" />
      </div>
    </div>
  )
}
