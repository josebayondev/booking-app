// El QueryClient de TanStack Query y sus opciones por defecto: cómo se comporta ante un
// error toda consulta de la aplicación mientras no diga lo contrario.

import { QueryClient } from '@tanstack/react-query'

/**
 * Comprueba si un error trae un código de estado HTTP.
 *
 * La capa `api/` todavía no existe (llega en su propia subtarea), así que esto no se ata a
 * ninguna clase concreta: describe el contrato mínimo que sus errores tendrán que cumplir
 * — exponer un `status` numérico — y hasta entonces se queda en `false` sin romper nada.
 */
function hasHttpStatus(error: unknown): error is { status: number } {
  return (
    typeof error === 'object' &&
    error !== null &&
    'status' in error &&
    typeof (error as { status: unknown }).status === 'number'
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
       * Reintentar un 4xx es tirar peticiones a la basura: un 409 (hueco ya reservado) o un
       * 429 (rate limit del backend) no cambian porque insistas, y con el 429 solo empeoras.
       * Los fallos de red y los 5xx sí merecen otra oportunidad — el backend corre en el
       * plan gratuito de Render y su arranque en frío ronda los 40 s, así que la primera
       * petición de una visita puede caer por timeout con el servicio perfectamente sano.
       */
      retry: (failureCount, error) => {
        if (hasHttpStatus(error) && error.status >= 400 && error.status < 500) {
          return false
        }
        return failureCount < 2
      },
      // La disponibilidad cambia cuando otro reserva, no cada segundo. Medio minuto evita
      // la ráfaga de refetches al navegar sin llegar a enseñar huecos ya ocupados; la
      // consulta que necesite otra cosa lo sobreescribe en su propio hook.
      staleTime: 30_000,
    },
  },
})
