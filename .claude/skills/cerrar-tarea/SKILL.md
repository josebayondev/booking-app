---
name: cerrar-tarea
description: Verifica que una tarea de booking-app está realmente terminada, la marca en ClickUp y reporta lo que falta. Úsala cuando el desarrollador diga que ha acabado algo, que el PR ya está mergeado, o pida marcar en ClickUp, revisar si está todo bien y ver qué queda.
---

# Cerrar el día: verificar, marcar y decir qué falta

Cierra el ciclo que abrió `siguiente-tarea`: comprueba con evidencia que el trabajo cumple
su DoD y está en `main`, actualiza el estado en ClickUp y deja claro qué queda por delante.

Lee primero `.claude/skills/clickup-booking-app.md` — el mapa del tablero y la regla de
estados están ahí.

## Procedimiento

### 1. Identificar la subtarea

Por el número que diga el desarrollador (`13.2`). Si no lo dice, dedúcela del último commit
de `main` y contrástala con el tablero, y **confirma cuál has elegido** antes de tocar
nada.

Si ya está cerrada, dilo y pasa directamente al paso 6: no la reescribas.

### 2. Verificar con evidencia, no de memoria

Ejecuta lo que corresponda al ámbito tocado y **pega el resultado real**. Desde `backend/`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

Desde `frontend/`:

```bash
npm run lint
npm run typecheck
npm run build
```

Si algo falla: dilo con la salida delante, **no cierres nada** y ofrece arreglarlo. Una
tarea cerrada con la suite en rojo es peor que una tarea abierta.

### 3. Comprobar el DoD, punto por punto

Saca el DoD literal de la descripción de la subtarea (`clickup_get_task` con
`include: ["description"]`) y ve uno a uno, señalando el test o el código concreto que lo
cumple — con `fichero:línea`. Si un punto del DoD no está cubierto por un test, cuéntalo
como **pendiente**, no como cumplido de otra manera.

### 4. Comprobar que está en `main` — este es el gate

```bash
git fetch origin --quiet && git log origin/main --oneline -10
```

Busca el commit del PR. Si el trabajo sigue en una rama o el PR está abierto, la subtarea
**no se marca**: se reporta como "lista, pendiente de merge". Comprueba también el estado
de la CI del PR (`gh pr checks`, o el MCP de GitHub) — un PR mergeado con CI roja tampoco
cierra.

### 5. Escribir en ClickUp, y solo ahora

- Lee los estados reales con `clickup_get_task(expand_statuses: true)`.
- Elige el primero de tipo `done`; si esa lista no tiene ninguno, el de tipo `closed`.
  Cerrar con `complete` donde existe `terminada` esconde la tarea del tablero.
- Aplícalo con `clickup_update_task`.
- Si con esta subtarea quedan **todas** las del FEAT padre cerradas, cierra también el FEAT.
- Opcional, útil para el rastro: un comentario en la tarea con el número de PR.

### 6. Decir qué falta

- Subtareas que siguen pendientes en el FEAT en curso.
- **Cuál es la siguiente** — el punto de entrada de `siguiente-tarea` mañana.
- Lo que hayas detectado durante la verificación y no esté en el tablero: deuda, un caso
  sin test, una decisión que quedó a medias. **Propónlo, no lo crees** en ClickUp por tu
  cuenta.

### 7. Documentación

Si el cambio ha tocado arquitectura — una capa nueva, un middleware, una convención — la
sección "Arquitectura" de `CLAUDE.md` tiene que reflejarlo. Este repo ya lleva ese hábito
(ver el commit `548c621`). Si falta, dilo aquí y ofrece escribirlo.

## Límites

- **Nada de git que escriba** (`add`, `commit`, `push`, `merge`, `rebase`, `reset`) ni
  ningún comando `alembic`. Leer el estado de git sí (`status`, `diff`, `log`, `fetch`).
- Nunca marques cerrado lo que no has verificado tú en esta sesión.
