# .claude/

Configuración de Claude Code específica de este proyecto. Se va rellenando cuando el patrón
correspondiente se repite de verdad, no antes (ver `CLAUDE.md` para el resto de convenciones
del proyecto). Por ahora solo hay skills; `hooks/`, `commands/` y `agents/` siguen vacíos.

- **`settings.json`** — permisos y hooks compartidos por cualquiera que abra este repo con
  Claude Code (se commitea).
- **`settings.local.json`** (no existe todavía, y si aparece **no se commitea** — ver
  `.gitignore`) — overrides personales de cada desarrollador.
- **`hooks/`** — scripts a los que apuntan los hooks definidos en `settings.json`. Úsalos
  cuando una regla tiene que cumplirse sí o sí, mecánicamente, sin depender de que el modelo
  decida obedecer. Ejemplos concretos para este repo: bloquear `git commit`/`push` y
  cualquier comando `alembic` (hoy son solo instrucción en `CLAUDE.md`, un hook los
  convierte en regla dura), formatear con `ruff format` tras cada edit, o evitar que se
  cuele un secreto en un commit.
- **`skills/`** — flujos propios de este proyecto que se repiten y merecen empaquetarse
  como procedimiento reutilizable, invocable por nombre o por contexto. Se añaden cuando el
  flujo se ha repetido 2-3 veces de verdad, no antes — meter algo especulativo aquí sin
  haber visto el patrón repetirse es sobre-ingeniería. Las que hay:
  - **`siguiente-tarea/`** — abre el día: lee el tablero de ClickUp, elige la siguiente
    subtarea y prepara el plan para implementarla, con su DoD y los ficheros que toca.
  - **`cerrar-tarea/`** — cierra el ciclo: verifica lint, tipos y tests, comprueba el DoD y
    que el PR está en `main`, marca la tarea en ClickUp y reporta lo que falta.
  - **`clickup-booking-app.md`** — no es una skill, es la referencia que leen las dos: IDs
    de las listas, cómo se organizan FEAT y subtareas, y la regla de estados. Cuando cambie
    el tablero se actualiza este fichero, no las skills.
- **`commands/`** — atajos directos de un solo prompt para cosas que el desarrollador quiere
  disparar a mano tecleando `/algo`. A diferencia de un skill, no es un procedimiento
  complejo de varios pasos — es una plantilla de prompt corta y explícita.
- **`agents/`** — subagentes a medida para cuando una tarea es tan grande o aislada que
  conviene delegarla a un contexto/permisos aparte, en vez de ensuciar la conversación
  principal con el ruido de sus pasos intermedios.

Orden mental de más ligero a más pesado, de cara a decidir dónde meter algo nuevo:
`CLAUDE.md` (instrucción simple) → `hooks` (cumplimiento forzoso) → `skills` (procedimiento
reutilizable) → `commands` (atajo manual) → `agents` (delegación aislada).

`.mcp.json` (en la raíz del repo, no aquí dentro) — servidores MCP de proyecto, compartidos
vía git (p. ej. ClickUp/GitHub) en vez de depender de la config personal de cada uno.

Lo que llene esta carpeta acaba siendo el esqueleto de la plantilla para futuros proyectos,
así que la vara de medir es esa: se sube aquí lo que ya se ha demostrado que se repite en un
proyecto de este tipo (API + Postgres + frontend separado), no lo que parece que se va a
repetir.
