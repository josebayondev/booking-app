// Todo el copy de la landing pública (`/`) en un solo objeto. Las secciones lo reciben por
// props y no escriben ni una frase por su cuenta, así que cambiar el mensaje es editar
// este fichero y nada más.
//
// Lo que vive en la base de datos -- la duración de la cita, los horarios, la antelación
// mínima -- deliberadamente NO está aquí: lo edita el dueño desde el panel y una copia en
// el código se quedaría vieja sin que nadie se entere. Eso llega por la API.

/** Los iconos son componentes de React, y aquí solo va dato serializable: cada sección
 * resuelve el nombre a su componente. */
export type IconName = 'calendar' | 'clock' | 'check' | 'list'

/** Un enlace de navegación interna, para `<Link to>`. */
export interface Cta {
  label: string
  to: string
}

/** Un ancla dentro de la misma página, que no es una ruta y por tanto no es un `Cta`. */
export interface AnchorCta {
  label: string
  href: string
}

export interface LandingContent {
  hero: {
    eyebrow: string
    /** Una entrada por línea: el corte del titular se decide aquí, no en el navegador. */
    title: string[]
    subtitle: string
    bullets: { icon: IconName; title: string; description: string }[]
    primary: Cta
    secondary: AnchorCta
    note: string
  }
  stats: {
    /** Texto y no número: hay valores con unidad ("1 min"). */
    value: string
    label: string
  }[]
  process: {
    eyebrow: string
    title: string
    steps: { title: string; body: string }[]
  }
  appointmentTypes: {
    title: string
    subtitle: string
    errorMessage: string
    retryLabel: string
    emptyMessage: string
  }
  faq: {
    eyebrow: string
    title: string
    items: { question: string; answer: string }[]
  }
  finalCta: {
    title: string[]
    body: string
    primary: Cta
    note: string
  }
}

export const landing: LandingContent = {
  hero: {
    eyebrow: 'Reserva en menos de un minuto',
    title: ['Reserva una reunión conmigo.', 'Sin cuentas ni esperas.'],
    subtitle:
      'Elige el tipo de cita, un hueco libre y confírmalo al momento. Sin registrarte, sin ida y vuelta de emails.',
    bullets: [
      {
        icon: 'calendar',
        title: 'Reserva directa',
        description: 'Sin registro',
      },
      {
        icon: 'clock',
        title: 'Confirmación al momento',
        description: 'Sin esperar un email',
      },
      {
        icon: 'list',
        title: 'Duración clara',
        description: 'Sin sorpresas',
      },
    ],
    primary: { label: 'Reservar una cita', to: '/reservar' },
    secondary: { label: 'Ver tipos de cita', href: '#tipos-de-cita' },
    note: 'Disponibilidad esta semana',
  },

  // Hechos del servicio, comprobables en la propia página. Aquí no van métricas de uso:
  // no las hay, e inventarlas sería mentir en la cara del producto.
  stats: [
    { value: '0', label: 'cuentas que crear' },
    { value: '3', label: 'pasos hasta la confirmación' },
    { value: '1 min', label: 'para reservar' },
  ],

  process: {
    eyebrow: 'Cómo funciona',
    title: 'Tres pasos y ya está',
    steps: [
      {
        title: 'Eliges el tipo de cita',
        body: 'Cada uno tiene su propia duración, y la ves antes de elegir hora.',
      },
      {
        title: 'Eliges un hueco libre',
        body: 'Solo aparecen los huecos realmente disponibles, en hora peninsular.',
      },
      {
        title: 'Confirmas y listo',
        body: 'Te llevas un enlace propio de la cita para consultarla o cancelarla. Sin contraseña.',
      },
    ],
  },

  appointmentTypes: {
    title: 'Qué puedes reservar',
    subtitle:
      'Cada tipo de cita tiene su propia duración. Elige el que mejor encaje.',
    errorMessage:
      'No se han podido cargar los tipos de cita. Puede que el servicio esté arrancando -- inténtalo de nuevo en unos segundos.',
    retryLabel: 'Reintentar',
    emptyMessage: 'Todavía no hay tipos de cita configurados.',
  },

  faq: {
    eyebrow: 'Dudas frecuentes',
    title: 'Lo que suelen preguntarme',
    items: [
      {
        question: '¿Tengo que crearme una cuenta?',
        answer:
          'No. Eliges hueco, dejas tu nombre y tu email, y ya está. No hay registro ni contraseña en ninguna parte.',
      },
      {
        question: '¿Cómo consulto la cita después?',
        answer:
          'Al confirmar te llevas un enlace propio de tu cita. Guárdalo: desde ahí puedes verla en cualquier momento.',
      },
      {
        question: '¿Y si al final no puedo asistir?',
        answer:
          'Cancela desde el enlace de tu cita en cuanto lo sepas. El hueco vuelve a quedar libre para otra persona.',
      },
      {
        question: '¿Con cuánta antelación puedo reservar?',
        answer:
          'El calendario ya te enseña solo lo que se puede reservar: los huecos demasiado próximos o demasiado lejanos no aparecen.',
      },
      {
        question: '¿Qué datos guardas de mí?',
        answer:
          'Tu nombre, tu email y el motivo si decides escribirlo. Nada más, y solo para gestionar la cita.',
      },
      {
        question: '¿La reunión es por videollamada?',
        answer:
          'Sí. Si prefieres otra cosa, dímelo en el motivo al reservar y lo hablamos.',
      },
    ],
  },

  finalCta: {
    title: ['Cuéntame tu proyecto.', 'Empezamos por una llamada.'],
    body: 'Una primera conversación para entender qué necesitas y decirte con franqueza si puedo ayudarte.',
    primary: { label: 'Reservar una cita', to: '/reservar' },
    note: 'Sin cuentas. Sin compromiso.',
  },
}
