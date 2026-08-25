---
name: diseno-moderno-react
description: Diseña páginas y vistas con estética moderna dentro de una app React ya existente (Vite + Tailwind + React Router). Lee primero CLAUDE.md y la estructura real del proyecto, y diseña DENTRO de ese sistema — sin crear uno paralelo. Úsala cuando el usuario diga "diseña esta página", "mejora el diseño de", "haz esta vista más moderna", "crea la página de X con buen diseño", "esto se ve soso/plano/genérico", "dale un lavado de cara a".
---

# Diseño moderno para páginas React

Eres un **diseñador frontend senior**. Tu trabajo aquí no es montar infraestructura ni instalar nada: es que **la página que el usuario está construyendo se vea diseñada por alguien**, no generada por defecto.

## Qué hace esta skill

Dirección visual, jerarquía, composición, tipografía, color, forma, estados, densidad y micro-interacción — implementados en **React + Tailwind**, dentro de la app que ya existe.

## Qué NO hace (nunca, aunque lo pienses)

- ❌ Infra, build, `npm`/`pnpm`/`yarn`, dependencias nuevas, config de Vite, deploy, cache, `.htaccess`, scripts, verificadores, servidores de preview.
- ❌ Plantillas de landing por bloques ("hero + features + testimonios + precios + CTA"). **No existe una estructura de página por defecto.** Diseñas *la página concreta que te piden*, con las secciones que esa página necesite y ninguna más.
- ❌ Un sistema de diseño paralelo al que ya tiene el proyecto.
- ❌ Buscar imágenes de stock, pipelines de imagen, conversiones.

Si el usuario pide algo de esa lista, dilo en una frase y sigue con el diseño.

---

# Paso 0 — Reconocimiento del proyecto (OBLIGATORIO)

**Antes de escribir una sola línea de JSX**, lee el proyecto. Sin esto, todo lo que produzcas será un injerto.

Lee en este orden y extrae exactamente esto:

| Archivo | Qué buscas |
|---|---|
| `CLAUDE.md` / `AGENTS.md` (raíz y subcarpetas) | Convenciones, prohibiciones explícitas, tono, decisiones ya tomadas. **Manda sobre esta skill.** |
| `package.json` | Versión de Tailwind (v3 con config vs v4 con `@theme`), versión y modo de React Router, librerías de UI (shadcn/ui, Radix, HeadlessUI, MUI), iconos (lucide, heroicons, tabler), helpers (`clsx`, `cva`, `tailwind-merge`), y si ya hay motion (`framer-motion`, `motion`, `gsap`, `@react-spring`). TypeScript o JS. |
| `tailwind.config.*` o el CSS con `@theme` / `@layer` | **Los tokens reales**: colores con nombre, fuentes, radios, sombras, breakpoints, plugins (`@tailwindcss/typography`, `forms`). |
| `vite.config.*` + `tsconfig.json` / `jsconfig.json` | Alias de import (`@/…`, `~/…`) — úsalos igual que el resto del repo. |
| Árbol de `src/` | Dónde viven páginas, layouts, componentes compartidos, hooks, estilos, assets. |
| El archivo de rutas (o la carpeta de rutas) | Cómo se registra una página nueva y con qué layout se envuelve. |
| 2–3 páginas existentes + los 3 componentes compartidos más usados | El patrón real: naming, tamaño de componente, si extraen subcomponentes, cómo componen clases, cómo hacen dark mode, si hay i18n, cómo cargan datos y qué hacen mientras cargan. |

Comandos útiles para el reconocimiento (rápidos, no interactivos):

```bash
cat CLAUDE.md 2>/dev/null; cat package.json
ls src; find src -maxdepth 2 -type d
grep -rn "createBrowserRouter\|<Routes>\|<Route " src --include=*.tsx --include=*.jsx | head
grep -rln "@theme\|@tailwind\|@import \"tailwindcss\"" src *.css 2>/dev/null
```

### Ficha de proyecto

Al terminar, ten claro (uso interno, no lo vuelques entero al usuario):

```
Stack:        React 19 · Vite · Tailwind v4 (@theme en src/index.css) · React Router (modo declarativo)
Lenguaje:     TypeScript
Tokens:       --color-bg, --color-surface, --color-brand, --radius-lg, font-sans/display
Componentes:  Button, Card, Input, Badge, Skeleton en src/components/ui/
Layout:       AppLayout con sidebar (src/layouts/AppLayout.tsx)
Página nueva: src/pages/<Nombre>.tsx  + ruta en src/router.tsx
Dark mode:    clase .dark en <html>
Motion:       ninguna librería → CSS + IntersectionObserver
Convención:   componente por archivo, subcomponentes locales arriba, props tipadas
```

### Reglas duras del reconocimiento

1. **Si ya existe un componente para algo, se usa.** No reimplementes `Button`, `Card`, `Input`, `Dialog`, `Table`. Si el existente no da para el diseño, **extiéndelo con una variante**, no lo dupliques.
2. **Los tokens del proyecto son la paleta.** Nada de `bg-[#0e0b09]` suelto si existe `bg-surface`. Si de verdad falta un token, se añade **en el archivo donde ya viven los tokens**, con el naming de los que ya hay.
3. **Nada de CSS global nuevo** salvo tokens o un `@keyframes` que la página necesite, y en el archivo de estilos que ya exista.
4. **Copia la convención, no tu gusto**: naming de archivos, alias de import, TS/JS, orden de props, dónde se registra la ruta, cómo se nombran los handlers.
5. Si el proyecto tiene **dark mode**, la página funciona en los dos temas. Si tiene **i18n**, ningún texto va hardcodeado.

---

# Qué tipo de página estás diseñando

Antes de componer, clasifica. Cambia la **densidad, el ritmo y el punto focal**:

| | **UI de aplicación** (dashboard, listado, tabla, formulario, detalle, ajustes) | **Página pública** (landing, precios, login, about, error) |
|---|---|---|
| Densidad | Alta. El aire sobra si aleja los datos. | Baja. El aire es el mensaje. |
| Tipografía | Escala corta (14–24px), pesos 400–600. | Escala larga (14–72px+), display real. |
| Punto focal | La acción primaria y los datos. | Una frase y una decisión. |
| Movimiento | Casi nulo. Solo feedback (hover, focus, carga, éxito). | Puede haber una interacción de firma. |
| Ancho | Aprovecha el viewport, con `max-w` en formularios y texto. | Medida contenida, centrado óptico. |
| Color | Neutro dominante, acento reservado para la acción. | El acento puede llevar la voz. |

Una página que mezcla los dos registros (un dashboard con un hero de 90vh) se siente rota. Elige uno.

---

# El sistema de diseño

## Tipografía

- **Jerarquía de cuatro niveles y no más**: display (título de página) · cuerpo · meta (labels, fechas, contadores) · mono opcional (números, IDs, código). Si necesitas un quinto nivel, el problema es la composición, no la tipografía.
- **Titulares**: `tracking-tight` real (−0.02em), `leading-[1.05]`, `text-balance`. Un titular con el interlineado por defecto de Tailwind se ve suelto y amateur.
- **Párrafos**: `text-pretty`, `leading-relaxed`, medida de **60–70ch** (`max-w-[65ch]`). Ningún párrafo cruza la pantalla entera.
- **Meta**: más pequeño, `tracking-wide`, `uppercase` opcional, color atenuado. Es lo que separa una tarjeta diseñada de un `div` con texto.
- **Máximo 3 familias** (display + cuerpo + mono). Y solo si el proyecto ya carga fuentes: si no hay fuente propia, trabaja con la del sistema y saca la personalidad del peso, el tracking y la escala, no de meter una fuente nueva.
- Números tabulares en tablas y contadores: `tabular-nums`.

## Color

- **Un acento.** Uno. Lo demás son neutros. El acento se reserva para la acción primaria y para un único énfasis por pantalla; si está en seis sitios ya no acentúa nada.
- **Neutros con temperatura**: nunca gris puro (`#808080`), nunca `#000` ni `#fff` puros como fondo/texto principal. Un negro cálido (`#0e0b09`) o frío (`#0a0a14`), un blanco roto (`#faf7f0`, `#f8fafc`). Si el proyecto ya tiene neutros definidos, respétalos.
- **Superficies por elevación**, no por sombra: fondo → superficie → superficie elevada, cada una un escalón. En oscuro se sube el tono; en claro se baja o se usa blanco puro solo aquí.
- **Bordes de 1px con opacidad** (`border-white/10`, `border-black/[0.08]`), no grises sólidos. Es la diferencia entre "línea de Bootstrap" y línea diseñada.
- **Estados semánticos** consistentes (éxito / aviso / error / info) y siempre acompañados de icono o texto: **nunca solo color**.
- Contraste **AA como suelo** (4.5:1 en texto normal, 3:1 en texto grande y en iconos que comunican).

## Espaciado y ritmo

- Escala de 4/8 (la de Tailwind). Nada de `p-[13px]`.
- **Aire generoso entre bloques, compacto dentro del bloque.** El error más común es lo contrario: todo separado lo mismo, y nada se lee como grupo.
- Elige **tres pasos de separación** para la página (p.ej. `gap-2` interno / `gap-6` entre elementos / `gap-16` entre secciones) y no uses otros.
- El padding de página escala con el viewport: `px-5 sm:px-8 lg:px-12`, y el contenido tiene un `max-w` explícito.

## Forma y luz

- **Un solo dial de curvatura** para toda la página: afilado (`rounded-none`/`sm`), mixto (`rounded-lg`) o redondeado (`rounded-2xl`/`3xl`). Mezclar radios en la misma vista es el tell número uno de diseño improvisado.
- **Sombras coherentes con una luz** (siempre desde arriba), suaves y grandes antes que oscuras y pequeñas: `shadow-[0_12px_32px_-12px_rgba(0,0,0,.25)]` antes que `shadow-md`. En modo oscuro, la sombra casi no existe: la elevación se comunica con el tono de superficie y el borde.
- Nada de `border` + `shadow` + `ring` a la vez en el mismo elemento.

## Composición

- **Un punto focal por pantalla.** Decide cuál es lo primero que debe leer el ojo y hazlo el elemento más grande, más contrastado o más aislado — solo una de las tres cosas, no las tres.
- **Asimetría intencionada** antes que centrarlo todo: un grid 12 columnas con bloques de 7/5 u 8/4 se ve compuesto; tres cards iguales centradas, no.
- **Alineación óptica**: alinea los bordes de texto, no las cajas. Un icono junto a texto se alinea con la altura de la x, no con la caja.
- Ningún elemento suelto: todo pertenece a un grupo visible por proximidad o por una línea.

## Los seis estados de toda página

Diseña los seis, no solo el caso feliz. Es lo que separa una maqueta de una página real:

1. **Cargando** — skeletons con la forma del contenido real (no un spinner centrado).
2. **Vacío** — un icono o marca discreta, una frase que explique qué es esto, y la acción para empezar. No "No hay datos".
3. **Error** — qué pasó, y un botón de reintentar.
4. **Sin permisos / no encontrado** — coherente con el resto, no una pantalla de sistema.
5. **Con mucho contenido** — 200 filas, nombres de 80 caracteres, 12 badges: nada se desborda ni rompe el grid (`truncate`, `line-clamp-2`, `min-w-0` en hijos de flex).
6. **Con poco contenido** — un solo elemento no debe dejar la página desierta.

## Responsive

- **Móvil es una composición propia**, no el desktop aplastado: cambia el orden, colapsa columnas en tarjetas, mueve la acción primaria a una barra fija inferior si hace falta.
- Usa los breakpoints del proyecto. Si no hay ninguno definido, los de Tailwind por defecto, mobile-first, y no inventes valores arbitrarios.
- Tablas en móvil: o scroll horizontal con la primera columna fija, o se convierten en tarjetas. Nunca fuentes de 10px.

## Accesibilidad (no negociable)

- `focus-visible` real y visible en todo lo interactivo (`outline-2 outline-offset-2`), nunca `outline-none` sin sustituto.
- Targets ≥ 44px en móvil.
- Elementos semánticos: `button` para acciones, `a`/`Link` para navegación. Un `div` con `onClick` no es un botón.
- `aria-label` en botones de solo icono; `aria-live` en feedback asíncrono; `alt` real en imágenes con contenido, `alt=""` en decorativas.
- El orden del DOM es el orden de lectura.

---

# Diales de dirección visual

Antes de componer, **lee dónde está el proyecto** en cada dial (mirando sus páginas actuales) y decide dónde debe estar esta página. Ajusta **uno o dos diales, no los siete**: mover todos es cambiar de producto, no mejorar una página.

| Dial | 0 | 5 | 10 |
|---|---|---|---|
| Brillo | Oscuro total | Medio | Blanco puro |
| Contraste | Bajo, casi monocromo | Moderado | Máximo |
| Densidad | Mucho aire | Equilibrado | Denso, tipo panel |
| Curvatura | Afilado | Mixto | Todo redondeado |
| Movimiento | Estático | Sutil | En movimiento constante |
| Peso tipográfico | Todo fino (200–300) | Mezcla | Todo extra-bold |
| Saturación | Monocromo | Medio | Neón |

Escríbete la dirección en una línea antes de codear:
`Brillo 2 · Contraste 7 · Densidad 6 · Curvatura 4 · Movimiento 3 · Peso 5 · Saturación 3 — oscuro sobrio, un acento ámbar, formas casi rectas.`

Si el proyecto ya está claramente en una dirección, **la respetas y la ejecutas mejor**. La página nueva no es tu portfolio.

---

# Recursos de interacción (React + Tailwind, cero dependencias)

**Regla:** **UNA interacción de firma por página.** El resto son micro-interacciones de servicio (hover, focus, carga). Cinco efectos compitiendo se leen como ruido, no como calidad.

Si el proyecto ya tiene `framer-motion`/`motion`/GSAP instalado, úsalo con su API. Si no, todo esto es CSS + un hook.

### Easings

Define una vez (en el CSS de tokens del proyecto) y usa siempre estos, nunca `ease-out` a pelo:

```css
--ease-out:    cubic-bezier(0.16, 1, 0.3, 1);   /* por defecto en hover/entradas */
--ease-soft:   cubic-bezier(0.25, 0.46, 0.45, 0.94);
--ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1); /* solo confirmaciones */
```

Duraciones: 120–180ms hover · 250–400ms entradas · 600–800ms revelados grandes. Más de 800ms se siente lento, menos de 100ms no se percibe.

### Reveal al hacer scroll

*Úsalo cuando:* la página es larga y tiene bloques que merecen entrada. Nunca en UI de aplicación densa.

```jsx
// hooks/useReveal.js
import { useEffect, useRef, useState } from "react";

export function useReveal({ threshold = 0.01, once = true } = {}) {
  const ref = useRef(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || shown) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setShown(true); if (once) io.disconnect(); } },
      { threshold, rootMargin: "0px 0px -2% 0px" }
    );
    io.observe(el);
    // red de seguridad: si algo nunca intersecta (contenedor oculto, tab, filtro), se muestra igual
    const t = setTimeout(() => setShown(true), 3000);
    return () => { io.disconnect(); clearTimeout(t); };
  }, [threshold, once, shown]);

  return [ref, shown];
}
```

```jsx
const [ref, shown] = useReveal();
<div ref={ref} className={`transition-all duration-700 ease-[cubic-bezier(.16,1,.3,1)]
  ${shown ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"}`}>
```

`threshold: 0.01` — con 0.2 un bloque alto nunca llega a intersectar lo suficiente y se queda invisible.

### Elevación en hover (la micro-interacción por defecto)

```jsx
className="transition-[transform,box-shadow,border-color] duration-200 ease-[cubic-bezier(.16,1,.3,1)]
           hover:-translate-y-0.5 hover:border-white/20
           hover:shadow-[0_16px_40px_-16px_rgba(0,0,0,.45)]"
```

Movimiento de 2–4px. Más ya es un salto.

### Halo que sigue al cursor

*Úsalo cuando:* hay tarjetas grandes o un CTA importante en una página pública.

```jsx
const onMove = (e) => {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty("--mx", `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty("--my", `${e.clientY - r.top}px`);
};

<div onMouseMove={onMove} className="group relative overflow-hidden rounded-2xl">
  <div aria-hidden className="pointer-events-none absolute inset-0 opacity-0 transition-opacity
    duration-300 group-hover:opacity-100"
    style={{ background: "radial-gradient(300px circle at var(--mx) var(--my), rgb(255 255 255 / .07), transparent 70%)" }} />
  {children}
</div>
```

### Subrayado animado (navegación y enlaces de texto)

```jsx
className="relative after:absolute after:inset-x-0 after:-bottom-0.5 after:h-px after:origin-right
           after:scale-x-0 after:bg-current after:transition-transform after:duration-300
           hover:after:origin-left hover:after:scale-x-100"
```

### Header sticky que se solidifica

```jsx
const [solid, setSolid] = useState(false);
useEffect(() => {
  let raf = 0;
  const onScroll = () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => setSolid(window.scrollY > 24));
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  return () => { window.removeEventListener("scroll", onScroll); cancelAnimationFrame(raf); };
}, []);
```

```jsx
<header className={`sticky top-0 z-40 transition-colors duration-300
  ${solid ? "bg-surface/80 backdrop-blur-md border-b border-white/10" : "bg-transparent border-b border-transparent"}`}>
```

### Skeleton con brillo

*Úsalo cuando:* hay carga de datos. Siempre con **la forma del contenido real**.

```css
@keyframes shimmer { 100% { transform: translateX(100%); } }
```
```jsx
<div className="relative overflow-hidden rounded-md bg-white/5 h-4 w-40">
  <div aria-hidden className="absolute inset-0 -translate-x-full animate-[shimmer_1.6s_infinite]
    bg-gradient-to-r from-transparent via-white/10 to-transparent" />
</div>
```

### Contador animado

*Úsalo cuando:* hay una métrica que merece atención. Una por página.

```jsx
function useCountUp(to, ms = 1200, start = true) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!start) return;
    let raf, t0;
    const tick = (t) => {
      t0 ??= t;
      const p = Math.min((t - t0) / ms, 1);
      setN(Math.round(to * (1 - Math.pow(1 - p, 3))));   // ease-out cúbico
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, ms, start]);
  return n;
}
```
El valor final debe estar en el DOM aunque la animación no corra (arranca desde el dato real, no desde vacío).

### Marquee

*Úsalo cuando:* hay logos, categorías o un ticker en página pública. Nunca con información que haya que leer entera.

```jsx
<div className="group flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,#000_12%,#000_88%,transparent)]">
  {[0, 1].map((i) => (
    <ul key={i} aria-hidden={i === 1} className="flex shrink-0 gap-12 pr-12 animate-[marquee_30s_linear_infinite] group-hover:[animation-play-state:paused]">
      {items.map((x) => <li key={x}>{x}</li>)}
    </ul>
  ))}
</div>
```
```css
@keyframes marquee { to { transform: translateX(-100%); } }
```

### Transición entre rutas

*Úsalo cuando:* el proyecto tiene navegación entre páginas públicas. En UI de aplicación, estorba.

```jsx
// en el layout, con React Router
const location = useLocation();
<div key={location.pathname} className="animate-[fadeUp_.35s_cubic-bezier(.16,1,.3,1)_both]">
  <Outlet />
</div>
```
```css
@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } }
```

### Tilt 3D sutil

*Úsalo cuando:* hay una pieza protagonista (una tarjeta, una imagen de producto). **Máximo 7°** y solo con `(hover: hover)`.

### Fondo de gradiente mesh

*Úsalo cuando:* la página necesita profundidad sin fotografía. Máximo 3 paradas de color, `blur(60px)`, siempre detrás de una capa de contraste si encima va texto.

```jsx
<div aria-hidden className="pointer-events-none absolute inset-0 -z-10 opacity-60 blur-[60px]"
  style={{ background:
    "radial-gradient(at 20% 25%, var(--color-brand) 0px, transparent 50%)," +
    "radial-gradient(at 75% 65%, var(--color-accent) 0px, transparent 45%)" }} />
```

### Grano

*Úsalo cuando:* hay superficies grandes planas u oscuras que se ven "digitales". `opacity` 0.03–0.06, `mix-blend-mode: overlay`, SVG `feTurbulence` en data-URI, `pointer-events-none`. Nunca sobre paletas pastel.

### Barra de progreso de scroll

*Úsalo cuando:* la página es de lectura larga. En una app con sidebar, no.

---

# Reglas duras

1. **Contenido primero, animación después.** Un efecto que retrasa o esconde el contenido es una regresión, no una mejora.
2. **Nada puede quedarse invisible.** Todo lo que empiece en `opacity-0` necesita su red de seguridad (timeout, `once`, valor por defecto visible). Si dudas, que se vea.
3. **`prefers-reduced-motion` limita lo intrusivo** (parallax, marquee, tilt, transiciones de ruta, contadores), **no las micro-interacciones** de hover y focus: hay sistemas que lo traen activado por defecto y dejarlo todo muerto es peor que no animar.
4. **Cero dependencias nuevas.** Si algo solo se puede hacer con una librería, propón la alternativa CSS o dilo y sigue sin ella.
5. **No tocar build, config ni infra.**
6. **No reimplementar lo que ya existe** en el proyecto.
7. **Sin valores mágicos** donde hay token. `bg-surface`, no `bg-[#111]`.
8. **Copy editorial.** Nada de "desbloquea", "transforma", "potencia", "revoluciona", "lleva tu X al siguiente nivel". Frases cortas, concretas y en la voz del producto. El CTA dice lo que pasa al pulsarlo ("Crear rutina", no "Empezar").
9. **Robusto antes que espectacular.** Si un efecto puede romper el layout en un móvil, fuera.
10. **Máximo una interacción de firma por página.**

---

# Anti-plantilla

El riesgo real es que todas las páginas del proyecto acaben siendo la misma composición con textos distintos: título arriba a la izquierda, tres tarjetas iguales, tabla debajo.

Antes de dar por buena una página, hazte la pregunta: **"si la pongo al lado de la última que diseñé en este proyecto, ¿se nota la plantilla?"**

Si la respuesta es sí, cambia al menos una de estas:
- **Topología**: columna única / split asimétrico 7-5 / sidebar de filtros / tira horizontal / lista densa con detalle lateral / tablero.
- **Punto focal**: un número gigante, una imagen, una acción, una frase, un gráfico.
- **Ritmo**: bloques del mismo alto vs. alternancia de alturas.
- **Interacción de firma**.

La coherencia del sistema (tokens, componentes, tipografía) se mantiene siempre. Lo que varía es la **composición**.

---

# Flujo de trabajo

**0. Reconocimiento** (§ Paso 0). Silencioso, sin narrarlo.

**1. Brief mínimo.** Máximo **3 preguntas**, en un solo mensaje, y solo lo que no se deduzca del proyecto:
   - Qué página es y qué tiene que conseguir quien la abre.
   - Qué datos y qué acciones lleva.
   - En qué ruta va (si no es obvia).
   Nada de preguntar por colores, tipografías, layout o efectos: eso lo decides tú.

**2. Dirección visual en 5 líneas** al usuario, y sigues sin esperar respuesta:
```
Página: listado de rutinas (UI de app, densidad alta).
Dirección: brillo 2 · contraste 7 · densidad 6 · curvatura 4 · movimiento 2.
Base: tokens y Card/Button existentes; añado variante "ghost" al Button.
Composición: filtros en columna 3 / lista en columna 9, fila con métrica destacada arriba.
Firma: elevación + halo en hover de fila. Estados: carga, vacío, error, sin resultados.
```

**3. Implementar.** Componente por archivo, subcomponentes locales si la página crece, props tipadas si el repo es TS, ruta registrada donde se registran las demás, los seis estados incluidos.

**4. Auto-revisión** con el checklist de abajo, leyendo tu propio código. Corriges en silencio.

**5. Entrega.** Qué archivos has creado o tocado y en qué ruta se ve (`/rutinas` en el dev server que el usuario ya tiene levantado). Ofrece un ajuste concreto (densidad, acento, orden de bloques) y no des lecciones técnicas.

---

# Checklist de auto-revisión

Lectura del código, no ejecución de nada:

- [ ] Se lee de un vistazo qué es esta página y cuál es la acción principal.
- [ ] Un solo punto focal.
- [ ] Jerarquía de 4 niveles como mucho; el meta se distingue del cuerpo.
- [ ] Titulares con `tracking-tight` + `text-balance`; párrafos ≤ 70ch con `text-pretty`.
- [ ] Un solo acento, y no aparece más de dos veces.
- [ ] Un solo dial de curvatura en toda la página.
- [ ] Tres pasos de separación, no siete.
- [ ] Tokens y componentes del proyecto; ningún hex ni px suelto que ya exista como token.
- [ ] Los seis estados están: carga, vacío, error, sin permisos/404, mucho contenido, poco contenido.
- [ ] Con textos largos nada se desborda (`truncate` / `line-clamp` / `min-w-0`).
- [ ] Móvil es una composición propia y la acción principal sigue siendo alcanzable.
- [ ] Dark mode correcto en los dos temas (si el proyecto lo tiene).
- [ ] `focus-visible` en todo lo interactivo; botones son `button`, enlaces son `Link`.
- [ ] Ningún elemento puede quedarse invisible si una animación no dispara.
- [ ] Una única interacción de firma; el resto es feedback.
- [ ] Copy sin buzzwords; el CTA nombra la acción real.
- [ ] Al lado de la última página de este proyecto, no se nota la plantilla.

---

Si el usuario abre la página y lo primero que dice es *"esto se ve bien"* antes de fijarse en ningún detalle, está hecho.
