// El QueryClient de TanStack Query y sus opciones por defecto: cómo se comporta ante un
// error toda consulta de la aplicación mientras no diga lo contrario.

import { QueryClient } from '@tanstack/react-query'

/**
 * Comprueba si un error se declara a sí mismo como no reintentable.
 *
 * Es un contrato estructural, no un `instanceof`: `lib/` no puede importar de `api/` (ver
 * las capas en `CLAUDE.md`), así que la capa de servicios marca sus errores con un
 * `retryable` booleano y aquí solo se lee. Lo que no traiga la marca —el `TypeError` de un
 * fetch que no llegó a salir— se reintenta, que es lo que se quiere con una red que falla.
 */
function isNonRetryable(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'retryable' in error &&
    (error as { retryable: unknown }).retryable === false
  )
}

/**
 * Se crea una sola vez, a nivel de módulo, y no dentro de un componente: la caché vive en
 * esta instancia, así que recrearla en cada render la tiraría entera.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      /*
       * Insistir en un 4xx es tirar peticiones a la basura: un 409 (hueco ya reservado) o
       * un 429 (rate limit del backend) no cambian por repetir, y con el 429 solo empeoras.
       * Tampoco se reintenta una respuesta que incumple el contrato: si al backend le
       * falta un campo, le seguirá faltando. Los fallos de red y los 5xx sí merecen otra
       * oportunidad — el backend corre en el plan gratuito de Render y su arranque en frío
       * ronda los 40 s, así que la primera petición de una visita puede caer por timeout
       * con el servicio perfectamente sano.
       */
      retry: (failureCount, error) => {
        if (isNonRetryable(error)) return false
        return failureCount < 2
      },
      // La disponibilidad cambia cuando otro reserva, no cada segundo. Medio minuto evita
      // la ráfaga de refetches al navegar sin llegar a enseñar huecos ya ocupados; la
      // consulta que necesite otra cosa lo sobreescribe en su propio hook.
      staleTime: 30_000,
    },
  },
})
