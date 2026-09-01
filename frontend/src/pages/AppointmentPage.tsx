// Ruta `/cita/:token`: gestión de una cita ya reservada -- verla, cancelarla o
// reprogramarla. Es la URL a la que apunta el enlace del email de confirmación, así que
// casi siempre se abre en frío, pegada en la barra de direcciones. El acceso va por
// token opaco y nunca por un id secuencial, para que nadie pueda pasearse por las citas
// ajenas cambiando un número.
import { useParams } from 'react-router'

import { ApiError } from '../api/http.ts'
import BookingCalendar from '../components/BookingCalendar.tsx'
import TimeSlotList from '../components/TimeSlotList.tsx'
import { useAppointmentManagement } from '../features/booking/useAppointmentManagement.ts'
import { formatLocalDate, formatLocalTime } from '../lib/formatDateTime.ts'

export default function AppointmentPage() {
  // `noUncheckedIndexedAccess` obliga a contar con que no venga; la ruta garantiza que sí,
  // pero el tipo no lo sabe.
  const { token } = useParams<{ token: string }>()
  const {
    booking,
    cancellation,
    isRescheduling,
    startReschedule,
    cancelReschedule,
    availability,
    selectedDate,
    selectDate,
    selectedSlot,
    selectSlot,
    daySlots,
    reschedule,
    confirmReschedule,
  } = useAppointmentManagement(token ?? '')

  if (booking.isPending) {
    return <p className="text-sm text-stone-500">Cargando tu cita…</p>
  }

  if (booking.isError) {
    const message =
      booking.error instanceof ApiError
        ? booking.error.detail
        : 'No se ha podido cargar tu cita. Puede que el enlace sea incorrecto.'
    return <p className="text-sm text-red-600">{message}</p>
  }

  const appointment = booking.data
  const isCancelled = appointment.status === 'cancelled'

  return (
    <div className="max-w-xl">
      <h2 className="text-2xl font-bold">Tu cita</h2>
      <p className="mt-1 text-sm text-stone-500">
        Referencia {appointment.reference}
      </p>

      <dl className="mt-6 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
        <dt className="font-semibold text-stone-700">Tipo</dt>
        <dd>{appointment.appointmentTypeName}</dd>
        <dt className="font-semibold text-stone-700">Fecha</dt>
        <dd>{formatLocalDate(appointment.startsAt)}</dd>
        <dt className="font-semibold text-stone-700">Hora</dt>
        <dd>{formatLocalTime(appointment.startsAt)} (tu zona horaria)</dd>
        <dt className="font-semibold text-stone-700">Estado</dt>
        <dd>{isCancelled ? 'Cancelada' : 'Confirmada'}</dd>
      </dl>

      {isCancelled ? (
        <p className="mt-6 text-sm text-stone-500">
          Esta cita está cancelada. Si quieres reservar de nuevo, vuelve a la
          página de reserva.
        </p>
      ) : (
        <div className="mt-6 flex flex-col gap-4">
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              disabled={cancellation.isPending}
              onClick={() => {
                cancellation.mutate()
              }}
              className="rounded-xl border border-black/8 bg-surface px-4 py-2 text-sm font-semibold text-stone-700 transition-colors hover:bg-stone-100 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {cancellation.isPending ? 'Cancelando…' : 'Cancelar cita'}
            </button>

            {!isRescheduling && (
              <button
                type="button"
                onClick={startReschedule}
                className="rounded-xl bg-stone-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-stone-800"
              >
                Reprogramar
              </button>
            )}
          </div>

          {cancellation.isError && (
            <p className="text-sm text-red-600">
              {cancellation.error instanceof ApiError
                ? cancellation.error.detail
                : 'No se ha podido cancelar la cita. Inténtalo de nuevo.'}
            </p>
          )}

          {isRescheduling && (
            <div className="rounded-xl border border-black/8 bg-surface p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-stone-700">
                  Elige el nuevo horario
                </h3>
                <button
                  type="button"
                  onClick={cancelReschedule}
                  className="text-sm text-stone-500 hover:text-stone-700"
                >
                  Cancelar
                </button>
              </div>

              <div className="mt-4">
                <BookingCalendar
                  days={availability.data ?? []}
                  selectedDate={selectedDate}
                  onSelectDate={selectDate}
                />
              </div>

              {selectedDate !== null && (
                <div className="mt-4">
                  <TimeSlotList
                    slots={daySlots}
                    selectedSlot={selectedSlot}
                    onSelect={selectSlot}
                  />
                </div>
              )}

              {reschedule.isError && (
                <p className="mt-3 text-sm text-red-600">
                  {reschedule.error instanceof ApiError
                    ? reschedule.error.detail
                    : 'No se ha podido reprogramar la cita. Inténtalo de nuevo.'}
                </p>
              )}

              <button
                type="button"
                disabled={selectedSlot === null || reschedule.isPending}
                aria-label="Confirmar nuevo horario"
                onClick={confirmReschedule}
                className="mt-4 inline-flex w-fit items-center rounded-xl bg-stone-900 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {reschedule.isPending
                  ? 'Confirmando…'
                  : 'Confirmar nuevo horario'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
