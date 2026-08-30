// Ruta `/reservar`: el flujo de reserva. Elige fecha y hora sobre la disponibilidad real,
// pide los datos y confirma -- toda la orquestación vive en useBookingWizard, esta página
// solo la lee y compone con los componentes de presentación de components/.
import { ApiError } from '../api/http.ts'
import BookingCalendar from '../components/BookingCalendar.tsx'
import BookingConfirmation from '../components/BookingConfirmation.tsx'
import BookingForm from '../components/BookingForm.tsx'
import TimeSlotList from '../components/TimeSlotList.tsx'
import { useBookingWizard } from '../features/booking/useBookingWizard.ts'

export default function BookingPage() {
  const {
    appointmentTypes,
    selectedType,
    selectType,
    availability,
    selectedDate,
    selectDate,
    selectedSlot,
    selectSlot,
    daySlots,
    creation,
    confirmBooking,
  } = useBookingWizard()

  if (creation.isSuccess) {
    return <BookingConfirmation booking={creation.data} />
  }

  if (appointmentTypes.isError) {
    return (
      <div className="flex flex-col items-start gap-3 rounded-2xl border border-black/8 bg-surface p-6">
        <p className="text-stone-600">
          No se han podido cargar los tipos de cita. Puede que el servicio esté
          arrancando -- inténtalo de nuevo en unos segundos.
        </p>
        <button
          type="button"
          onClick={() => void appointmentTypes.refetch()}
          className="inline-flex items-center rounded-xl border border-black/8 bg-page px-4 py-2 text-sm font-semibold text-stone-700 transition-colors hover:bg-stone-100"
        >
          Reintentar
        </button>
      </div>
    )
  }

  if (appointmentTypes.isLoading) {
    return <p className="text-stone-500">Cargando tipos de cita…</p>
  }

  // Más de un tipo activo y ninguno elegido todavía: hay que preguntar antes de poder
  // pedir disponibilidad, porque GET /availability la exige.
  if (selectedType === null) {
    return (
      <div>
        <h2 className="text-2xl font-bold text-stone-900">
          Elige el tipo de cita
        </h2>
        <ul className="mt-6 flex flex-col gap-3">
          {appointmentTypes.data?.map((type) => (
            <li key={type.slug}>
              <button
                type="button"
                onClick={() => {
                  selectType(type)
                }}
                className="w-full rounded-xl border border-black/8 bg-surface px-4 py-3 text-left transition-colors hover:bg-stone-100"
              >
                <span className="font-semibold text-stone-900">
                  {type.name}
                </span>
                <span className="ml-2 text-sm text-stone-500">
                  {type.durationMinutes} min
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  const creationErrorMessage = creation.isError
    ? creation.error instanceof ApiError
      ? creation.error.detail
      : 'Ha ocurrido un error inesperado. Inténtalo de nuevo.'
    : null

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h2 className="text-2xl font-bold text-stone-900">
          Elige fecha y hora
        </h2>
        <p className="mt-2 text-stone-600">{selectedType.name}</p>
      </div>

      {availability.isError ? (
        <div className="flex flex-col items-start gap-3 rounded-2xl border border-black/8 bg-surface p-6">
          <p className="text-stone-600">
            No se ha podido cargar la disponibilidad. Inténtalo de nuevo.
          </p>
          <button
            type="button"
            onClick={() => void availability.refetch()}
            className="inline-flex items-center rounded-xl border border-black/8 bg-page px-4 py-2 text-sm font-semibold text-stone-700 transition-colors hover:bg-stone-100"
          >
            Reintentar
          </button>
        </div>
      ) : (
        <BookingCalendar
          days={availability.data ?? []}
          selectedDate={selectedDate}
          onSelectDate={selectDate}
        />
      )}

      {selectedDate !== null && (
        <TimeSlotList
          slots={daySlots}
          selectedSlot={selectedSlot}
          onSelect={selectSlot}
        />
      )}

      {selectedSlot !== null && (
        <BookingForm
          onSubmit={({ customerName, customerEmail }) => {
            confirmBooking(customerName, customerEmail)
          }}
          isSubmitting={creation.isPending}
          errorMessage={creationErrorMessage}
        />
      )}
    </div>
  )
}
