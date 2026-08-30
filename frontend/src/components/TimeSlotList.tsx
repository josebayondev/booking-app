// Selector de hora dentro de un día ya elegido: pinta cada hueco en la hora local de quien
// mira la pantalla, con el aviso explícito de que la cita es en hora peninsular española --
// el cuidado que pide FEAT 21, para que nadie en Canarias o Argentina se presente a la hora
// equivocada.
import type { FreeSlot } from '../api/availability.ts'
import { formatLocalTime } from '../lib/formatDateTime.ts'

interface TimeSlotListProps {
  slots: FreeSlot[]
  selectedSlot: FreeSlot | null
  onSelect: (slot: FreeSlot) => void
}

export default function TimeSlotList({
  slots,
  selectedSlot,
  onSelect,
}: TimeSlotListProps) {
  if (slots.length === 0) {
    return (
      <p className="text-sm text-stone-500">
        No hay horas libres este día. Elige otra fecha.
      </p>
    )
  }

  return (
    <div>
      <p className="text-xs text-stone-500">
        Horas en tu zona horaria local. La cita es en hora peninsular española
        (Europe/Madrid).
      </p>
      <ul className="mt-3 flex flex-wrap gap-2">
        {slots.map((slot) => {
          const isSelected =
            selectedSlot?.startsAt.getTime() === slot.startsAt.getTime()
          return (
            <li key={slot.startsAt.toISOString()}>
              <button
                type="button"
                aria-pressed={isSelected}
                onClick={() => {
                  onSelect(slot)
                }}
                className={`rounded-xl border px-4 py-2 text-sm font-semibold transition-colors ${
                  isSelected
                    ? 'border-stone-900 bg-stone-900 text-white'
                    : 'border-black/8 bg-surface text-stone-700 hover:bg-stone-100'
                }`}
              >
                {formatLocalTime(slot.startsAt)}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
