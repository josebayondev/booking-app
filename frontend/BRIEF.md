# Brief — landing pública `/`

Contrato de contenido de la home. Si cambia el enfoque, se actualiza esto primero.

## Público y objetivo

Alguien que llega desde LinkedIn con un proyecto en la cabeza y quiere hablarlo. No conoce
el producto y no va a crear una cuenta para nada.

**Objetivo:** que reserve una reunión. **Acción principal:** `Reservar una cita` → `/reservar`.
Todo lo demás en la página existe para quitar fricción a ese botón.

**Voz:** primera persona, la de Jose. Frases cortas y concretas. Cero buzzwords.

## Secciones, en orden

| #   | Sección                                                                            | De dónde sale el contenido      |
| --- | ---------------------------------------------------------------------------------- | ------------------------------- |
| 1   | **Hero** tipográfico: titular, subtítulo, chips de beneficio, 2 botones, microcopy | copy                            |
| 2   | **Stats**: tres datos del servicio                                                 | copy                            |
| 3   | **Proceso**: cómo funciona en 3 pasos                                              | copy                            |
| 4   | **Tipos de cita**: rejilla con sus estados de carga, error y vacío                 | **API** (`useAppointmentTypes`) |
| 5   | **FAQ**: 6 preguntas con `<details>`                                               | copy                            |
| 6   | **CTA final**: repite la acción antes de cerrar                                    | copy                            |
| 7   | **Footer**: marca, descripción, contacto por `mailto:`, copyright                  | copy                            |

Siete secciones. Fuera del brief y por tanto fuera de esta entrega: logos de clientes,
pricing, galería, equipo, testimonios y formulario de contacto.

## Los stats, y por qué estos

No hay métricas de uso reales en la base de datos, así que **no invento tracción**. Los tres
números son hechos del servicio, comprobables mirando la página:

- **0** cuentas que crear
- **3** pasos hasta la confirmación
- **1 min** para reservar

Lo que sí está en la base de datos — la duración de la cita, los horarios, la antelación
mínima — **no entra aquí**: lo edita el dueño desde el panel y se quedaría viejo. Eso viene
de la API, en la sección 4.

## Decisiones que hay que confirmar

1. **El footer se monta en `App.tsx`, junto al `Header`**, así que sale en las cuatro rutas
   públicas (`/`, `/reservar`, `/cita/:token`, 404) y no en `/admin`. Es el mismo cromo
   público que la cabecera; un footer que solo aparece en la home se ve roto al navegar.
   Se sale un pelo del "solo la landing", pero son tres líneas.
2. **Sin enlaces legales.** Aviso legal, privacidad y cookies llegan cuando haya textos de
   verdad; enlazarlos a rutas que no existen es peor que no ponerlos.
3. **`src/content/landing.ts` es una capa nueva.** Al crearla, su regla se apunta en la
   sección "Capas del frontend" de `CLAUDE.md`.

## Fuera de alcance

El panel de administración (lo rehace FEAT 24), el wizard de reserva, la decisión de
prerender de FEAT 20 y el `og:url` pendiente en `index.html`. Son cabos sueltos reales,
pero cada uno es su propia tarea.
