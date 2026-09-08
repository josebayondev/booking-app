# Catálogo de secciones

Cada entrada: para qué sirve → anatomía → forma de las props. **Una página pública buena
tiene entre 5 y 8 secciones**; más es scroll vacío.

Tipos compartidos que se repiten abajo:

```ts
type Cta = { label: string; to: string }   // `to` de <Link>, no href
```

---

## Hero
**Siempre.** Es el 80% de la decisión de quien entra.

Anatomía: eyebrow → h1 grande en dos líneas → subtítulo de ≤2 líneas → chips de beneficio →
botón primario + secundario → microcopy de tranquilidad ("sin registro", "cancela cuando
quieras").

```ts
{ eyebrow?: string; title: string[]; highlight?: number; subtitle: string;
  bullets?: string[]; primary: Cta; secondary?: Cta; note?: string }
```

`title` es un array de líneas porque el corte se decide en el contenido, no dejándoselo al
navegador: un titular grande partido por donde toque se lee mucho mejor. `highlight` es el
índice de la línea que lleva el énfasis.

Variantes: **tipográfica** (sobria, sin imagen), **con captura** del producto, **con foto a
sangre**.

---

## Servicios / Features en columnas
Tres columnas con icono, título y párrafo. La opción sobria y la que menos se rompe.

```ts
{ title?: string[]; items: { Icon: ComponentType<{ className?: string }>;
  title: string; body: string }[] }
```

Los iconos salen de `components/icons.tsx`; se pasa el componente, no un string.

---

## Bento
Rejilla asimétrica de 5-6 tarjetas donde una o dos ocupan doble ancho. Más carácter que las
columnas, y encaja bien con la elevación en hover.

```ts
{ eyebrow?: string; title: string[];
  items: { Icon: ComponentType; title: string; body: string; wide?: boolean }[] }
```

---

## Proceso
Pasos numerados con línea conectora. Para cuando la gente no sabe qué va a pasar si pulsa el
botón — que es justo el caso de una reserva sin registro.

```ts
{ title?: string[]; steps: { num: number; title: string; body: string }[] }
```

---

## Stats
Banda de 3-4 números grandes. Solo si los números son concretos y ciertos. Si se animan, con
`useCountUp` (está en `diseno-moderno-react`) y el valor final siempre presente en el DOM.

```ts
{ items: { value: number; suffix?: string; label: string }[] }
```

---

## Showcase sticky
Izquierda: pasos que se iluminan al hacer scroll. Derecha: panel `sticky` que cambia. Es la
sección más vistosa del catálogo y la más fácil de romper en móvil, donde colapsa a vertical.

Necesita un `IntersectionObserver`; en React va en un hook propio, en la línea de `useReveal`.
No es una sección para empezar: móntala solo si la página ya funciona sin ella.

```ts
{ eyebrow?: string; title: string[];
  steps: { num: number; title: string; body: string; bullets?: string[] }[] }
```

---

## Tabla de datos
Horarios, cuadro de tarifas, comparativa. Infrautilizada y muy convincente: los datos reales
generan confianza.

Va dentro de un contenedor con `overflow-x-auto` — la tabla scrollea, la página nunca. Y
`tabular-nums` en las columnas numéricas.

```ts
{ title?: string; columns: string[]; rows: (string | number)[][]; note?: string }
```

---

## Testimonios
Dos formatos: **una cita gigante** centrada (más potente) o **rejilla de tres** tarjetas.
Nombre real y rol. Sin foto es mejor que con foto de stock.

```ts
type Testimonial = { text: string; name: string; role: string; initials: string }
{ quote?: Testimonial; items?: Testimonial[] }
```

---

## Equipo
Nombre, rol y una línea de credencial. Con `initials` como respaldo cuando no hay foto.

```ts
{ title?: string[];
  members: { name: string; role: string; credential?: string;
             photo?: string; initials: string }[] }
```

---

## Galería
Rejilla de fotos. Imprescindible si el negocio es un espacio físico; ruido si no lo es.
`loading="lazy"` y `alt` descriptivo en todas.

```ts
{ title?: string; images: { src: string; alt: string; wide?: boolean }[] }
```

---

## FAQ
Acordeón con `<details><summary>` — cero JS y accesible de serie. 5-8 preguntas de las que
la gente hace de verdad.

```ts
{ title?: string[]; items: { q: string; a: string }[] }
```

---

## Mapa y horarios
Dirección, horario por días, teléfono con `tel:` y email con `mailto:`. Para el mapa, un
iframe de OpenStreetMap o una imagen estática enlazada a Google Maps; nunca la API de Maps
en una página pública.

```ts
{ address: string; city: string; hours: { days: string; time: string }[];
  phone: string; email: string; mapEmbed?: string }
```

---

## CTA final
Bloque a ancho completo con titular grande y los mismos botones del hero. Cierra la página
antes del footer, siempre.

```ts
{ eyebrow?: string; title: string[]; body?: string; primary: Cta; secondary?: Cta }
```

---

## Footer
Marca y descripción más columnas de enlaces, con una barra inferior de copyright. **En
España los enlaces legales son obligatorios**: aviso legal, privacidad y cookies.

```ts
{ description: string; columns: { title: string; links: Cta[] }[]; legal: string }
```

---

## Secciones que casi nunca aplican aquí

- **Logos / confianza.** Solo con nombres reconocibles de verdad. Tres logos inventados
  hacen más daño que ninguno.
- **Pricing.** Un cuadro de planes pide un precio público y un catálogo; un sistema de citas
  con un solo tipo de cita no lo tiene. Si hay tarifas, van en una **tabla de datos**.
- **Formulario de contacto.** Duplica la acción principal: aquí la conversión es reservar,
  no escribir un email. Si hace falta contacto, basta con `mailto:` en el footer.

---

## Combinaciones recomendadas

**Sistema de reserva de citas (esta app):**
Hero tipográfico → Proceso ("cómo funciona", 3 pasos) → tipos de cita (datos de la API, no
del contenido) → FAQ → CTA final → Footer.

Otras, para cuando la skill se reutilice en otro producto:

- **Servicio profesional:** Hero → Servicios → Proceso → Equipo → Testimonios → FAQ → CTA
- **Espacio físico:** Hero con foto → Stats → Bento → Tabla de horarios → Galería →
  Testimonios → Mapa → CTA
- **Producto digital:** Hero con captura → Stats → Showcase sticky → Bento → Testimonio →
  FAQ → CTA
