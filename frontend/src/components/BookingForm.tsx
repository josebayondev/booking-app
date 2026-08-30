// Formulario de datos del último paso: nombre y email, con el botón deshabilitado
// mientras se envía -- la mitigación barata del doble submit que pide FEAT 21 (el 409 de
// verdad lo garantiza el EXCLUDE de BD, esto es solo UX).
import { useState } from 'react'

interface BookingFormProps {
  onSubmit: (data: { customerName: string; customerEmail: string }) => void
  isSubmitting: boolean
  errorMessage: string | null
}

export default function BookingForm({
  onSubmit,
  isSubmitting,
  errorMessage,
}: BookingFormProps) {
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSubmit({ customerName, customerEmail })
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div>
        <label
          htmlFor="customer-name"
          className="block text-sm font-medium text-stone-700"
        >
          Nombre
        </label>
        <input
          id="customer-name"
          type="text"
          required
          value={customerName}
          onChange={(event) => {
            setCustomerName(event.target.value)
          }}
          className="mt-1 w-full rounded-xl border border-black/8 bg-surface px-4 py-2 text-sm text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
        />
      </div>

      <div>
        <label
          htmlFor="customer-email"
          className="block text-sm font-medium text-stone-700"
        >
          Email
        </label>
        <input
          id="customer-email"
          type="email"
          required
          value={customerEmail}
          onChange={(event) => {
            setCustomerEmail(event.target.value)
          }}
          className="mt-1 w-full rounded-xl border border-black/8 bg-surface px-4 py-2 text-sm text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
        />
      </div>

      {errorMessage !== null && (
        <p className="text-sm text-red-600">{errorMessage}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        aria-label="Confirmar reserva"
        className="inline-flex w-fit items-center rounded-xl bg-stone-900 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSubmitting ? 'Confirmando…' : 'Confirmar reserva'}
      </button>
    </form>
  )
}
