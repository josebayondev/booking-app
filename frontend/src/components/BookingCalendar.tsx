// Selector de fecha: un botón por cada día del rango ya pedido a GET /availability, solo
// pulsable si ese día tiene algún hueco libre. Grid propio con Tailwind, sin librería de
// calendario -- el rango ya viene acotado por el backend (62 días como mucho).
import type { DayAvailability } from '../api/availability.ts'
import { formatCalendarDay } from '../lib/formatDateTime.ts'

interface BookingCalendarProps {
  days: DayAvailability[]
  selectedDate: string | null
  onSelectDate: (date: string) => void
}

export default function BookingCalendar({
  days,
  selectedDate,
  onSelectDate,
}: BookingCalendarProps) {
  return (
    <ul className="grid grid-cols-3 gap-2 sm:grid-cols-5 md:grid-cols-7">
      {days.map((day) => {
        const hasSlots = day.slots.length > 0
        const isSelected = day.date === selectedDate
        return (
          <li key={day.date}>
            <button
              type="button"
              disabled={!hasSlots}
              aria-pressed={isSelected}
              onClick={() => {
                onSelectDate(day.date)
              }}
              className={`w-full rounded-xl border px-2 py-2 text-center text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                isSelected
                  ? 'border-stone-900 bg-stone-900 text-white'
                  : 'border-black/8 bg-surface text-stone-700 enabled:hover:bg-stone-100'
              }`}
            >
              {formatCalendarDay(day.date)}
            </button>
          </li>
        )
      })}
    </ul>
  )
}
