// Ruta `/admin/login`: la pantalla a la que lleva "Acceder como admin" en el Header. La
// barrera real es require_role en el backend (FEAT 14) -- esto solo pide las credenciales.
import { useState } from 'react'
import { useNavigate } from 'react-router'

import { ApiError } from '../api/http.ts'
import { useLogin } from '../features/auth/useLogin.ts'

export default function AdminLoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const login = useLogin()

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    login.mutate(
      { email, password },
      {
        onSuccess: () => {
          void navigate('/admin', { replace: true })
        },
      },
    )
  }

  const errorMessage = login.isError
    ? login.error instanceof ApiError
      ? login.error.detail
      : 'Ha ocurrido un error inesperado. Inténtalo de nuevo.'
    : null

  return (
    <div className="mx-auto max-w-sm">
      <h2 className="text-2xl font-bold text-stone-900">Acceso al panel</h2>
      <p className="mt-2 text-stone-600">
        El único rol que existe, sin registro.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <div>
          <label
            htmlFor="admin-email"
            className="block text-sm font-medium text-stone-700"
          >
            Email
          </label>
          <input
            id="admin-email"
            type="email"
            required
            value={email}
            onChange={(event) => {
              setEmail(event.target.value)
            }}
            className="mt-1 w-full rounded-xl border border-black/8 bg-surface px-4 py-2 text-sm text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
          />
        </div>

        <div>
          <label
            htmlFor="admin-password"
            className="block text-sm font-medium text-stone-700"
          >
            Contraseña
          </label>
          <input
            id="admin-password"
            type="password"
            required
            value={password}
            onChange={(event) => {
              setPassword(event.target.value)
            }}
            className="mt-1 w-full rounded-xl border border-black/8 bg-surface px-4 py-2 text-sm text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-stone-900"
          />
        </div>

        {errorMessage !== null && (
          <p className="text-sm text-red-600">{errorMessage}</p>
        )}

        <button
          type="submit"
          disabled={login.isPending}
          className="inline-flex w-fit items-center rounded-xl bg-stone-900 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-stone-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {login.isPending ? 'Accediendo…' : 'Acceder'}
        </button>
      </form>
    </div>
  )
}
