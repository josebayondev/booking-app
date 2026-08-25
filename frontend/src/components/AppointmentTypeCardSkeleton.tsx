// Estado de carga de una tarjeta de tipo de cita: mismas proporciones que la tarjeta
// real, para que la sección no salte de tamaño cuando llegan los datos. Pensado para el
// arranque en frío de Render (~40 s en la primera petición).

function ShimmerLine({ className }: { className: string }) {
  return (
    <div
      className={`relative overflow-hidden rounded-full bg-stone-200 ${className}`}
    >
      <div
        aria-hidden
        className="absolute inset-0 -translate-x-full animate-[shimmer_1.6s_infinite] bg-linear-to-r from-transparent via-white/70 to-transparent"
      />
    </div>
  )
}

export default function AppointmentTypeCardSkeleton() {
  return (
    <div
      role="status"
      aria-label="Cargando tipo de cita"
      className="flex flex-col rounded-2xl border border-black/8 bg-surface p-6"
    >
      <ShimmerLine className="h-3 w-16" />
      <ShimmerLine className="mt-3 h-5 w-2/3" />
      <ShimmerLine className="mt-3 h-4 w-full" />
      <ShimmerLine className="mt-1.5 h-4 w-4/5" />
      <ShimmerLine className="mt-6 h-4 w-20" />
    </div>
  )
}
