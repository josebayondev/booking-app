// Confirmación tras el 201 de POST /bookings: referencia y fecha/hora, sin navegar a
// /cita/:token -- esa página sigue siendo un placeholder hasta que 13.3/13.4 aterricen en
// el backend.
import type { Booking } from '../api/bookings.ts'
import { formatLocalDate, formatLocalTime } from '../lib/formatDateTime.ts'

interface BookingConfirmationProps {
  booking: Booking
}

export default function BookingConfirmation({
  booking,
}: BookingConfirmationProps) {
  return (
    <div className="rounded-2xl border border-black/8 bg-surface p-6">
      <h3 className="text-lg font-semibold text-stone-900">
        ¡Reserva confirmada!
      </h3>
      <p className="mt-2 text-stone-600">
        {formatLocalDate(booking.startsAt)} a las{' '}
        {formatLocalTime(booking.startsAt)} (tu hora local)
      </p>
      <p className="mt-4 text-sm text-stone-500">
        Referencia:{' '}
        <span className="font-mono font-semibold text-stone-900">
          {booking.reference}
        </span>
      </p>
      <p className="mt-2 text-sm text-stone-500">
        Guarda esta referencia. Todavía no hay una página para gestionar la cita
        por enlace -- llegará pronto.
      </p>
    </div>
  )
}
