// Hook de TanStack Query sobre POST /api/v1/admin/login: al ir bien, guarda la sesión en
// authStore. La navegación tras el login la decide la propia página, no este hook.

import { useMutation } from '@tanstack/react-query'

import { login } from '../../api/auth.ts'
import { useAuthStore } from './authStore.ts'

export function useLogin() {
  const setSession = useAuthStore((state) => state.login)

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      login(email, password),
    onSuccess: (data) => {
      setSession(data.accessToken)
    },
  })
}
