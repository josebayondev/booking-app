# Referencia de ClickUp para booking-app

El mapa del tablero de este proyecto: qué IDs tiene cada lista, cómo está organizado el
trabajo y cómo se cierra una tarea sin que desaparezca del tablero. Lo leen las skills
`siguiente-tarea` y `cerrar-tarea` para no redescubrirlo con llamadas MCP cada día.

## Dónde está el tablero

Workspace `90121621006`, espacio **Booking-app** `90128761052`.

| Ámbito | Lista | ID |
| --- | --- | --- |
| Carpeta **Backend** (`901213166474`) | API y dominio | `901220533165` |
| | Testing backend | `901220533166` |
| Carpeta **Frontend** (`901213166476`) | Base y landing | `901220533169` |
| | Panel admin | `901220533170` |
| | Testing frontend | `901220533172` |
| Sueltas en el espacio | Infra | `901220294594` |
| | Seguridad | `901220295489` |
| | Testing | `901220351924` |

## Cómo está organizado el trabajo

- La **tarea padre es un FEAT** (`FEAT 13 — API pública de reservas (sin login)`). Su
  descripción es el porqué del diseño: decisiones tomadas antes de escribir código, y hay
  que leerla antes de proponer nada, porque explica por qué las cosas son como son.
- El **trabajo ejecutable son las subtareas numeradas** (`13.2 Creación de reserva con
  token opaco`). Una subtarea es una unidad de entrega: una rama, un PR, un squash merge.
- El **DoD vive en la descripción de la subtarea**, normalmente en la última línea y
  literalmente con el prefijo `DoD:` — por ejemplo `DoD: reservar dos veces el mismo hueco
  devuelve 409, no un 500.`. Es el criterio de cierre, no una sugerencia.

Las descripciones no vienen completas en los listados: para leer una ficha de verdad hace
falta `clickup_get_task` con `include: ["description", "subtasks"]`.

## Estados: la trampa

Los estados **no son iguales en todas las listas**, así que nunca se escribe un nombre de
estado a ciegas:

- Las listas dentro de las carpetas Backend y Frontend heredan los del espacio: `to do`,
  `in progress`, `complete` — y `complete` es de tipo `closed`.
- `Infra` (y potencialmente otras listas sueltas) tiene además `terminada`, de tipo `done`.

**Regla de cierre**: leer los estados reales de la tarea con
`clickup_get_task(expand_statuses: true)` y elegir el primero de tipo `done`; solo si esa
lista no tiene ninguno, usar el de tipo `closed`. Cerrar con `complete` una tarea de una
lista que tiene `terminada` la esconde del tablero, que es justo lo que no se quiere.

## Correspondencia con el repositorio

- Una subtarea → una rama `feature/<nombre>` (o `fix/`, `chore/`) salida de `main`.
- Mensaje de commit en Conventional Commits, **una sola línea**: el prefijo (`feat:`,
  `fix:`...) en inglés, la descripción en español (ver "Idioma" en `CLAUDE.md`).
- Todo pasa por PR y solo squash merge. `main` está protegida.
- El número de PR queda en el commit de `main` (`feat(api): ... (#34)`), que es lo que
  permite atar una subtarea de ClickUp a su commit sin llevar la cuenta a mano.

## Mantenimiento

Si el tablero cambia — listas nuevas, un FEAT que se parte, estados que se renombran — se
actualiza **este fichero**, no las skills. Las skills describen el procedimiento; esto
describe el terreno.
