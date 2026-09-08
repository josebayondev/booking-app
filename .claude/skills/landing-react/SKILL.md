---
name: landing-react
description: Construye o rehace una página pública de marketing (la landing de `/`, una página de precios, una de "cómo funciona") dentro de esta app React + Vite, con el copy separado en un fichero tipado y la página compuesta por secciones de un catálogo. Úsala cuando el usuario diga "rehaz la landing", "la home se ve genérica", "moderniza la página pública", "añade una sección de X a la home", "monta la página de precios". Para vistas del panel de administración o del flujo de reserva, usa `diseno-moderno-react` en su lugar.
---

# Landing en React

Esta skill aporta **estructura y contenido** de una página pública: qué secciones lleva, en
qué orden y de dónde sale cada string.

**No aporta dirección visual.** Eso lo cubre `diseno-moderno-react` (tipografía, color,
espaciado, motion, los seis estados, accesibilidad, checklist). Léela y aplícala al escribir
el JSX; aquí no se repite nada de eso.

## Principio único

**El copy es dato, las secciones son renderizadores tontos.** Ningún texto de negocio vive
dentro de un componente. Cambiar la propuesta de valor tiene que ser editar un fichero, no
buscar frases por el `src/`.

Con una excepción que manda sobre la regla: **lo que viene de la API no entra en
`src/content/`**. Los tipos de cita, la disponibilidad y cualquier otra cosa del backend
siguen llegando por TanStack Query desde `features/`, por el mismo motivo por el que no van
en un store de Zustand — duplicarlos es cómo se quedan obsoletos sin que nadie se entere.
`src/content/` es solo copy escrito a mano.

## Qué NO hace

- Nada de dependencias nuevas, config de Vite, build ni deploy. Cero excepciones.
- Nada de Astro, MDX, CMS ni generadores de sitios: el stack es el que dice `CLAUDE.md`.
- Nada de imágenes de stock ni pipelines de imagen.
- Nada de meter secciones del catálogo "porque sí". Solo las que el brief eligió.

## Flujo

### Fase 1 — Entrevista

**Dos rondas como mucho, de ≤4 preguntas, con AskUserQuestion.** Esta app ya existe: el
negocio, el idioma, la paleta y el stack se leen del repositorio, no se preguntan.

Pregunta solo lo que no está escrito en ningún sitio:

- Ronda 1: a quién va dirigida la página, qué tiene que conseguir quien la abre, y cuál es
  la acción principal.
- Ronda 2: qué secciones del catálogo entran, y el contenido concreto de las que necesitan
  datos reales (precios, horarios, testimonios, números).

Cada opción que propongas es una recomendación con su motivo, para que se pueda aceptar
rápido. Si el usuario dice "hazlo tú" o "lo que veas", deja de preguntar, tira con los
valores por defecto y **di cuáles has asumido**.

Antes de la ronda 1, mira ClickUp: rehacer una página pública suele ser un FEAT con alcance
propio, y conviene no adelantarlo a medias.

### Fase 2 — Brief

Escribe un `BRIEF.md` **corto** (media pantalla) en `frontend/`: público, objetivo, acción
principal, secciones elegidas en orden, y qué contenido es copy y qué viene de la API.
Enséñalo y espera un sí antes de tocar código.

Si más adelante el usuario cambia el enfoque, se actualiza el brief primero.

### Fase 3 — Contenido

Escribe `frontend/src/content/<pagina>.ts` **antes que ningún componente**: un objeto
exportado y tipado, con el copy real en español, específico y en la voz del producto. Nada
de lorem ipsum, nada de "Característica 1", nada de buzzwords ("desbloquea", "potencia",
"lleva tu X al siguiente nivel").

Los tipos se declaran junto al objeto, en el mismo fichero, y salen de la forma real del
contenido — igual que en `api/` el tipo sale del schema y no se escribe una interfaz gemela
al lado.

`src/content/` es una capa nueva: la primera vez que la crees, añade su regla a la sección
"Capas del frontend" de `CLAUDE.md` — *copy de páginas públicas, un fichero por página, sin
lógica ni imports de `api/`* — igual que se hizo con `pages/` cuando llegó el router.

### Fase 4 — Secciones

Una sección por fichero en `frontend/src/components/sections/<Nombre>.tsx`, con sus props
tipadas. Elige del catálogo de `references/secciones.md`, que trae la anatomía y la forma de
los datos de cada una.

Las secciones son **componentes de presentación**, así que se rigen por la regla de
`components/` de `CLAUDE.md`: props en, JSX fuera, sin tocar `api/` ni TanStack Query. Una
sección que necesita datos del backend los recibe por props; quien llama al hook es la
página.

### Fase 5 — Composición

La página de `frontend/src/pages/` compone las secciones en el orden del brief y les pasa el
contenido. Su único trabajo es ese: tirar de los hooks de `features/` que hagan falta y
repartir props. Sin lógica propia.

### Fase 6 — Verificación

Desde `frontend/`, y reporta la salida real — nunca la des por buena:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Antes de decir que está listo:

- [ ] Los cuatro comandos pasan limpios.
- [ ] Cero strings de negocio fuera de `src/content/`.
- [ ] Responsive real a 390px, 768px y 1440px.
- [ ] Checklist de auto-revisión de `diseno-moderno-react` repasado.
- [ ] Ninguna sección incluida que no esté en el brief.

## Reglas duras

| Regla | Por qué |
|---|---|
| El copy solo en `src/content/` | Cambiar el mensaje = editar un fichero |
| Los datos de la API solo en TanStack Query | Duplicarlos en `content/` es garantizar que se queden viejos |
| Secciones sin estado, sin fetch, sin router | Se recolocan y reutilizan sin romper nada |
| Tokens en el `@theme` de `src/index.css`, nunca hex sueltos | Ya hay `--color-page` y `--color-surface`; se amplían ahí |
| Un fichero por sección, nombrado por lo que es | `Pricing.tsx`, no `Section3.tsx` |
| Cero dependencias nuevas | Si algo solo sale con una librería, propón la alternativa CSS y sigue |
| Navegación con `<Link>` de react-router | Un `<a href>` interno recarga la SPA entera |

## Errores comunes

- **Escribir componentes antes que el contenido.** Sale copy de relleno incrustado en el JSX
  y ya no hay quien lo saque.
- **Meter medio catálogo.** Una landing buena tiene entre 5 y 8 secciones; más es scroll
  vacío. Y hay secciones que directamente no aplican a este producto.
- **Copiar la landing de un SaaS.** Aquí no hay logos de clientes ni planes de precios que
  enseñar; poner tres logos inventados es peor que no poner ninguno.
- **Duplicar la cabecera.** `components/Header.tsx` ya existe: se usa, no se reimplementa.
