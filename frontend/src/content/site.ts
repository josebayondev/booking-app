// Copy del cromo común a todas las rutas públicas -- hoy solo el pie. Va aparte de
// `landing.ts` porque el pie sale en las cuatro rutas públicas, no solo en la home, y
// tenerlo en el contenido de una página concreta sería mentir sobre dónde se usa.

export interface SiteContent {
  footer: {
    description: string
    email: string
    repositoryUrl: string
    /** El nombre del titular; el año lo pone el pie en tiempo de render. */
    legalName: string
  }
}

export const site: SiteContent = {
  footer: {
    description:
      'Sistema de reservas de Jose Bayón, desarrollador fullstack. Hecho para no cruzar cinco emails hasta encontrar un hueco.',
    email: 'josebayondev@gmail.com',
    repositoryUrl: 'https://github.com/josebayondev/booking-app',
    legalName: 'Jose Bayón',
  },
}
