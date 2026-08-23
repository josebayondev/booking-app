---
name: siguiente-tarea
description: Elige la siguiente tarea de ClickUp del proyecto booking-app y prepara el plan para implementarla. Úsala cuando el desarrollador abra sesión preguntando qué toca hoy, pida mirar ClickUp, o nombre una carpeta (Backend, Frontend) o una lista del tablero sin más contexto.
---

# Abrir el día: elegir la siguiente tarea

Convierte el tablero de ClickUp en una tarea concreta lista para empezar: cuál toca, por
qué esa y no otra, qué la da por terminada y qué ficheros toca. No escribe código todavía.

Lee primero `.claude/skills/clickup-booking-app.md` — el mapa del tablero, los IDs de las
listas y las convenciones de estado están ahí, no aquí.

## Procedimiento

### 1. Fijar el ámbito

Si el desarrollador ha nombrado una carpeta (Backend, Frontend) o una lista, ese es el
ámbito. Si no lo ha dicho, **pregunta con `AskUserQuestion`** ofreciendo las carpetas y las
listas sueltas — no lo adivines: backend y frontend avanzan en paralelo y elegir por él
desperdicia el arranque de la sesión.

### 2. Leer el tablero

`clickup_filter_tasks` sobre las listas del ámbito, con `subtasks: true` e
`include_closed: true`. Hace falta ver lo cerrado además de lo pendiente: es lo que dice
por dónde iba el trabajo.

### 3. Elegir candidata

Por este orden:

1. La subtarea pendiente de número más bajo del FEAT que ya está empezado (tiene subtareas
   cerradas y subtareas pendientes).
2. Si no hay ninguno empezado, la primera subtarea del FEAT pendiente de número más bajo.
3. Respeta las dependencias declaradas en ClickUp si las hay, y las que estén escritas en
   la descripción (`la garantía real es el constraint de BD (5.5)`) aunque no estén
   modeladas como dependencia.

Si dos candidatas empatan de verdad, propón las dos con su porqué y deja elegir. Y si has
saltado por encima de algún FEAT anterior que sigue entero pendiente (hoy, `FEAT 11`),
menciónalo en una línea: saltárselo puede ser deliberado, pero que sea una decisión y no un
descuido.

### 4. Leer la ficha completa

`clickup_get_task` con `include: ["description", "subtasks"]` sobre:

- el **FEAT padre**, para el contexto de diseño y las decisiones ya tomadas;
- la **subtarea**, para el alcance concreto y el DoD literal.

Los listados truncan las descripciones — sin este paso estarías planificando a ciegas.

### 5. Contrastar con el repositorio antes de proponer nada

Mira `git log --oneline -15` y el código que la tarea toca. Dos cosas que se cazan aquí:
trabajo que ya está hecho y que el tablero no refleja, y patrones existentes que hay que
seguir en vez de inventar. Si algo de la tarea ya está implementado, dilo antes de
planificar — puede que lo que toque sea cerrarla, no hacerla.

### 6. Presentar

Un resumen corto, no un documento:

- **Qué toca** y por qué esa subtarea y no otra.
- **DoD literal** copiado de ClickUp, no parafraseado.
- **Ficheros** que se van a tocar, y qué se reutiliza de lo que ya existe (las funciones
  puras de `app/services/`, los helpers de `app/core/timezone.py`, las fixtures de
  `backend/tests/conftest.py`...).
- **Si hace falta una migración de Alembic**: dilo explícitamente, describe qué debería
  contener y **párate ahí** — las migraciones las genera y revisa el desarrollador.
- **Tests que hay que escribir**, junto a la lógica, no después.

### 7. Ofrecer marcar `in progress`

Antes de empezar, ofrece pasar la subtarea a `in progress` en ClickUp. Espera el visto
bueno; no lo hagas por tu cuenta.

### 8. Sugerir la rama y el commit

Cierra la presentación con dos sugerencias de texto — nunca las ejecutes tú, es el
desarrollador quien las lanza:

- El comando para crear la rama: `git checkout -b <tipo>/<nombre-en-kebab-case>`, con
  `<tipo>` de entre `feature`, `fix`, `chore`, `docs`, `test`, `refactor` (los mismos que
  Conventional Commits, ver `CLAUDE.md`) según la naturaleza de la subtarea, y
  `<nombre-en-kebab-case>` derivado de su título.
- Un adelanto del commit con el que probablemente cierre la subtarea, en el mismo formato
  de una sola línea: `<tipo>: <descripción corta>`. Es una plantilla orientativa a partir
  del DoD, no una promesa — el commit real lo escribe el desarrollador cuando el código
  esté listo, y puede que haga falta más de uno.

## Límites

- **Nada de git ni de alembic**: nunca ejecutes `checkout`, `add`, `commit`, `push`,
  `merge`, ni ningún comando `alembic`. Los ejecuta el desarrollador (ver `CLAUDE.md`).
  Sugerir el texto de los comandos de rama y commit (paso 8) no es una excepción a esto:
  se enseñan como texto para copiar, nunca se lanzan.
- No crees tareas nuevas en ClickUp. Si detectas algo que falta en el tablero, propónlo y
  deja que él decida.
- No amplíes el alcance de la subtarea. Si algo colindante parece necesario, sepáralo y
  dilo — probablemente sea un FEAT posterior que ya está planificado.
