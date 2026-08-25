# CLAUDE.md

Este fichero guía a Claude Code (claude.ai/code) cuando trabaja con el código de este
repositorio.

## Idioma

Todo lo que escribas va en **español**: las respuestas del chat, los comentarios de
código, los docstrings, los mensajes de error de los tests que expliquen algo, este mismo
fichero y cualquier documentación interna. Da igual en qué idioma esté el mensaje del
desarrollador.

Las cuatro excepciones, y no hay más:

- **`README.md`** se queda en inglés (es la cara pública del repositorio).
- **Los identificadores del código** —nombres de funciones, variables, clases, columnas,
  rutas— siguen en inglés.
- **Los nombres de rama y los mensajes de commit** siguen en inglés (ver "Convenciones").
- **Los mensajes de `logger.*` de la aplicación** siguen en inglés: son salida operativa
  que acaba en Sentry y en los logs de Render, y hay tests que comprueban sus subcadenas.
  Esto **no** incluye los mensajes de `assert` ni de `pytest.fail`, que explican algo a
  quien está desarrollando y por tanto van en español.

Además, **cada fichero empieza con una explicación corta y clara de lo que hace**: un
docstring de módulo en Python, un comentario de cabecera en YAML, Dockerfile, `.ini` o
`.env.example`. Corta de verdad: una o dos frases que digan para qué existe el fichero,
no un resumen de su contenido.

## Proyecto

Sistema de reserva de citas. Monorepo: `backend/` (FastAPI + SQLAlchemy + Alembic) y
`frontend/` (React + Vite + TypeScript). La reserva pública no tiene login; el panel de
administración sí está autenticado. El backend despliega en Render, el frontend en Vercel,
y la base de datos es Neon Postgres.

`backend/` tiene el esqueleto de la aplicación (instancia de `FastAPI`, `/health`,
configuración, Docker), Alembic con sus migraciones, los modelos de configuración de dominio
(tipos de cita y disponibilidad) y su seed, más los workflows de CI. `frontend/` tiene el
andamiaje de Vite + React + TypeScript con Tailwind, la separación de carpetas entre UI y
lógica, un store de Zustand de ejemplo y el `QueryClientProvider` de TanStack Query; sigue
sin rutas, sin páginas y sin cliente HTTP. Con ese andamiaje despertó la CI del frontend,
que hasta entonces estaba escrita pero dormida.

## Comandos que NO debes ejecutar

Estos los ejecuta el desarrollador. Escribe el código y los ficheros, y después párate y
dile qué tiene que ejecutar — no los lances tú nunca:

- `git add`, `git commit`, `git push`, `git merge`, `git rebase`, `git reset`
- **Cualquier comando `alembic`**, incluidos `revision`, `revision --autogenerate`,
  `upgrade` y `downgrade`. Tampoco crees ni edites ficheros de migración dentro de
  `alembic/versions/` — el desarrollador genera y revisa él mismo cada migración.
- Cualquier comando que despliegue, o que escriba en una base de datos remota

Sí puedes leer el estado de git (`git status`, `git diff`, `git log`).

Cuando un cambio requiera una migración, dilo explícitamente y describe qué debería
contener esa migración — y ahí párate.

## Comandos del backend

Se ejecutan desde `backend/`:

Las dependencias se gestionan con **uv**, y `uv.lock` está commiteado — fija cada
dependencia transitiva, así que local, CI y la imagen de Docker instalan versiones
idénticas. uv se instala con `brew install uv` (o `pip install uv` dentro del venv).

```bash
uv sync --extra dev             # crea/actualiza .venv desde uv.lock (versiones exactas)
uv run uvicorn app.main:app --reload   # servidor de desarrollo: http://localhost:8000, docs en /docs
uv run ruff check .             # lint
uv run ruff format .            # formato
uv run mypy app                 # tipos (modo estricto)
uv run pytest                   # tests (necesita Postgres: docker compose up -d postgres)
uv run pytest -m "not db"       # el subconjunto que no necesita base de datos
uv run pip-audit                # audita las deps bloqueadas contra la base de avisos de PyPI
```

Al cambiar dependencias — commitea siempre el `uv.lock` resultante en el mismo PR:

```bash
uv add <paquete>                # añade una dependencia de runtime (actualiza pyproject + lock)
uv add --optional dev <paquete> # añade una dependencia de desarrollo
uv lock --upgrade               # refresca cada pin a la última versión permitida
```

Ojo: `uv sync` deja el venv exactamente igual que el lock, así que borra todo lo que no
esté en él. CI y Docker usan `uv sync --frozen`, que falla en vez de volver a resolver
cuando `uv.lock` no está en sintonía con `pyproject.toml`.

## Comandos del frontend

Se ejecutan desde `frontend/`. Las dependencias se gestionan con **npm** — no yarn ni pnpm —
y `package-lock.json` está commiteado, igual que `uv.lock` en el backend. Que el gestor sea
npm no es preferencia: `frontend-ci.yml` cachea con `cache-dependency-path:
frontend/package-lock.json`, así que otro gestor rompería el caché de la CI.

```bash
npm install                     # instala desde package-lock.json
cp .env.example .env
npm run dev                     # servidor de desarrollo: http://localhost:5173
npm run lint                    # oxlint + prettier --check
npm run format                  # reescribe el formato con prettier
npm run typecheck               # tsc -b, en modo estricto
npm test                        # vitest run -- una pasada y sale
npm run test:watch              # vitest en watch, para desarrollar
npm run build                   # tsc -b && vite build
npm audit --audit-level=high    # audita las deps bloqueadas
```

`npm run lint` encadena `prettier --check` a propósito: meter el formato dentro de `lint`
es lo que hace que la CI lo verifique sin añadir un job solo para eso. Un job sí hizo falta
para los tests — `frontend-ci.yml` invoca `lint`, `typecheck`, `test`, `build` y `audit`
encadenados, y cada uno solo corre si el anterior pasó. Ojo con el script: `npm test` es
`vitest run` y no `vitest`, porque el modo watch dejaría el job colgado hasta morir por
timeout en vez de fallar.

## Docker / entorno local

```bash
docker compose up --build       # desde la raíz del repo: backend + postgres local juntos
docker build -t booking-backend ./backend   # solo la imagen del backend
```

Las credenciales del Postgres local de `docker-compose.yml`
(`postgres`/`postgres`/`booking_app`) son valores fijos de desarrollo, no secretos — no
tocan nunca datos reales y no aplican a Neon (staging/producción).

## Arquitectura

- **Configuración**: `app/core/config.py` — una clase `Settings` de `pydantic-settings`,
  cacheada con `get_settings()` (`lru_cache`), que lee `.env`. Cualquier configuración
  nueva dirigida por entorno va aquí. Qué fichero lee viene de `ENV_FILE` (por defecto
  `.env`); ponerlo a cadena vacía significa "no leas ningún fichero", que es como se sale
  la suite de tests — ver el punto de Tests más abajo. `ENV_FILE` deliberadamente **no**
  está en `.env.example`: es justo la variable que elige ese fichero.
- **Base de datos**: `app/core/db.py` tiene el `engine` de SQLAlchemy (construido desde
  `settings.database_url`, con el driver forzado a `postgresql+psycopg` vía `URL.set()` y
  `pool_pre_ping=True` porque Neon suspende el cómputo inactivo), la fábrica de sesiones
  `SessionLocal` y la dependencia generadora `get_db()` para usar con el `Depends()` de
  FastAPI. `app/main.py` registra un context manager `lifespan` que llama a
  `check_db_connection()` (`app/core/db.py`) — `engine.connect()` + `SELECT 1`, sin sesión
  del ORM — al arrancar, con reintentos y espera creciente, y falla rápido (lanza) si la
  base de datos es inalcanzable.
- **Zonas horarias**: `app/core/timezone.py` es el único sitio donde se convierte entre el
  reloj de pared local del dueño y UTC. Las reglas de disponibilidad guardan un `TIME`
  naive más un día de la semana; `local_to_utc()` las proyecta sobre una fecha concreta, y
  `local_day_bounds()` da los límites UTC de un día natural local. Los casos límite del
  cambio de hora están fijados por tests.
- **Capas de la API**: `app/api/` tiene los routers -- lo único que toca la sesión de base
  de datos y construye la respuesta HTTP -- y se registran en la app `FastAPI` desde
  `main.py` con `app.include_router(...)`. La lógica de negocio que no depende de
  SQLAlchemy vive en `app/services/` como funciones puras: sin sesión de BD, sin leer el
  reloj ni la configuración por su cuenta, todo entra por parámetro (ver
  `compute_free_slots` en `app/services/availability.py`) -- así se puede testear sin
  Postgres y queda reutilizable desde donde haga falta (el chatbot de FEAT 17, por
  ejemplo). `app/schemas/` tiene los contratos Pydantic de entrada y salida de cada ruta,
  con alias donde el nombre público de un query param no puede ser un identificador
  Python (`from`/`to` en `AvailabilityQuery`). Los errores de regla de negocio (no de
  forma de la petición) se lanzan como `ApiError` y se traducen a `{"code", "detail"}` por
  el handler de `app/core/errors.py` -- los 422 nativos de FastAPI/Pydantic se quedan con
  su formato de siempre, es una familia de error distinta. Todas las rutas públicas van
  bajo el prefijo `/api/v1` desde el primer endpoint (decidido en ClickUp antes de escribir
  código, FEAT 13) -- cambiarlo más tarde, con clientes de verdad enganchados, costaría
  mucho más.
- **Rate limiting**: `app/core/rate_limit.py` tiene `RateLimitMiddleware`, otro middleware
  ASGI puro (mismo motivo que el de cabeceras de seguridad: nada de `BaseHTTPMiddleware`)
  que limita las peticiones bajo `/api/v1` con una ventana deslizante en memoria -- sin
  Redis, ver Decisiones de arquitectura. Se registra el primero de los tres middlewares en
  `main.py`, o sea el más interno, para que una respuesta 429 salga ya con las cabeceras de
  CORS y de seguridad puestas. Identifica al cliente por `X-Forwarded-For` cuando
  `environment != "local"` (detrás hay un proxy de Render y el socket remoto es siempre el
  suyo) y por el socket remoto en local. Un tope de claves recordadas (`MAX_TRACKED_CLIENTS`)
  con desalojo LRU evita que el propio limitador sea un vector de agotamiento de memoria si
  alguien rota la IP falsificada en cada petición.
- **Cabeceras de seguridad**: `app/core/security_headers.py` tiene
  `SecurityHeadersMiddleware`, un middleware ASGI puro (no `BaseHTTPMiddleware`) que estampa
  `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` y una
  CSP en todas las respuestas. La CSP es `default-src 'none'` en todas partes — esta API
  solo devuelve JSON — salvo en `/docs`, `/docs/oauth2-redirect` y `/redoc`, que reciben una
  política relajada para que Swagger UI y ReDoc sigan cargando sus assets del CDN.
  `Strict-Transport-Security` se envía siempre que `environment != "local"`: Render termina
  el TLS y habla HTTP con el contenedor, así que no se puede decidir por el esquema de la
  petición, y mandar HSTS por `http://localhost` envenenaría la caché HSTS del navegador
  para cualquier otro proyecto local. Se registra **el último** en `main.py`, lo que lo
  convierte en el middleware más externo, así que las respuestas de preflight de CORS — que
  `CORSMiddleware` contesta sin llegar al router — también llevan las cabeceras.
- **Modelos**: `app/models/` tiene la `Base` declarativa con su convención de nombres, el
  `TimestampMixin` y los modelos de configuración de dominio (`AppointmentType`,
  `AvailabilityRule`, `AvailabilityException`). Todo modelo nuevo **tiene que** importarse
  en `app/models/__init__.py`: el autogenerate de Alembic solo ve las tablas cuyo módulo se
  ha importado, y si falta escribe una migración vacía sin avisar. `app/schemas/` sigue
  siendo andamiaje vacío para los esquemas Pydantic.
- **Seed**: `app/seed.py` inserta la configuración inicial (un tipo de cita y diez bloques
  de disponibilidad). Es idempotente por clave natural y **no actualiza filas existentes**:
  son los valores desde los que arranca una base de datos nueva, no valores que el seed
  mantenga a la fuerza.
- **Tests**: `backend/tests/conftest.py` aísla la suite del entorno antes de que nada
  importe `app.*` — vacía `ENV_FILE`, pone `DATABASE_URL` por defecto al Postgres de
  docker-compose (con `setdefault`, así que el valor propio de CI sigue ganando), fija
  `CORS_ORIGINS` a `TEST_CORS_ORIGIN` y fuerza `SENTRY_DSN` vacío para que una ejecución de
  tests no pueda llegar nunca al proyecto real de Sentry. El orden es crítico:
  `app/core/db.py` y `app/main.py` llaman a `get_settings()` en tiempo de import y
  `lru_cache` congela el resultado, así que ninguna fixture puede corregirlo después — por
  eso nada de `conftest.py` importa `app.*` a nivel de módulo. Sin esto, `uv run pytest`
  cogería `backend/.env` y correría contra la rama de desarrollo de Neon. Fixtures:
  `db_session` (una sesión dentro de una transacción que se deshace después, así que hasta
  un `commit()` del test se revierte, y que además vacía las tablas antes de empezar),
  `client`/`running_client` (la app real sin/con su lifespan, o sea sin/con conexión a base
  de datos), `api_client` (un `TestClient` cuyas rutas comparten la misma transacción que
  `db_session`, vía `app.dependency_overrides[get_db]` -- sin esto, `Depends(get_db)`
  abriría una conexión nueva en cada request, invisible a las filas que el test acaba de
  insertar; es el que usan los tests de endpoints que necesitan leer o escribir en la
  base de datos) y `clean_env`. Los tests que necesitan una base de datos viva llevan
  `@pytest.mark.db`. Ojo: `alembic/env.py` sí lee `.env` a propósito — lo que quieres es que
  `alembic upgrade head` migre la base de datos que tengas configurada.
- **Build de Docker**: `backend/Dockerfile` es un build en dos etapas — `builder` instala
  las dependencias bloqueadas en un venv en `/opt/venv` (con `uv sync --frozen
  --no-install-project`, así que solo se copian `pyproject.toml` + `uv.lock` y la instalación
  de dependencias no se invalida con cada cambio de código); `runtime` copia ese venv más el
  código de `app/` directamente del contexto de build. El proyecto en sí deliberadamente no
  se instala nunca como paquete — `app` es importable porque está en el directorio de
  trabajo. Corre como usuario sin privilegios y respeta `$PORT` (con 8000 de reserva) para
  Render, y por eso su CMD usa forma shell, para que la variable se expanda.
- **Fijado de versiones**: las dos etapas fijan `python:3.13-slim` por digest, y el binario
  de uv viene de una imagen `ghcr.io/astral-sh/uv` fijada por digest — mismo razonamiento
  que fijar las GitHub Actions por SHA. Dependabot (`.github/dependabot.yml`) mantiene al
  día el lockfile, los digests de las imágenes y los SHA de las actions.
- **Andamiaje del frontend**: `frontend/` sale de la plantilla `react-ts` de `create-vite`,
  con la demo del contador quitada. El lint lo hace **oxlint** (`.oxlintrc.json`) y el
  formato **Prettier** — oxlint es lo que genera hoy la plantilla oficial, y hace en
  TypeScript el mismo papel que Ruff en Python. Los `tsconfig` van más allá del template
  con `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride` y
  `exactOptionalPropertyTypes`: es el equivalente de `mypy --strict`. `tsconfig.json` no
  compila nada, solo referencia `tsconfig.app.json` (el código de `src/`) y
  `tsconfig.node.json` (`vite.config.ts`), y por eso el typecheck es `tsc -b` y no `tsc`.
  Solo las variables de entorno con prefijo `VITE_` llegan al navegador, así que ahí no va
  nunca un secreto.
- **Capas del frontend**: `src/api/` es el cliente HTTP y una función tipada por endpoint,
  `src/components/` son componentes de presentación puros (props en, JSX fuera, sin tocar
  `api/` ni TanStack Query), `src/features/` es la lógica por área — los hooks que envuelven
  TanStack Query y los stores de Zustand — y `src/lib/` las utilidades transversales. Cada
  carpeta lleva esa regla escrita en su `.gitkeep`. `src/pages/` se sumó con el router: un
  componente por ruta, y su único trabajo es componer — tira de los hooks de `features/` y
  pinta con los de `components/`, sin lógica propia. Es la quinta capa y llegó después que
  las otras cuatro, porque hasta que no hubo rutas no había nada que colgar de ella.
- **Rutas**: `react-router` en modo declarativo. El `BrowserRouter` va en `main.tsx`, por
  dentro del `QueryClientProvider` — la caché de consultas es independiente de la ruta y
  tiene que sobrevivir a la navegación — y la tabla de rutas vive en `App.tsx`. Se eligió
  frente a TanStack Router (que da params tipados de punta a punta) porque son cinco rutas
  planas y ningún dato se carga desde el router: de eso se encarga TanStack Query. La ruta
  comodín `*` no es adorno: con las rutas en cliente, un token mal copiado del email de
  confirmación aterriza ahí, y sin ella se quedaría mirando un layout vacío. Y ojo al
  desplegar: un SPA necesita que el hosting devuelva `index.html` en cualquier ruta, o
  entrar directo a `/cita/<token>` — que es justo la URL del email — da un 404.
- **Tests del frontend**: **Vitest** con Testing Library y `jsdom`, configurado dentro de
  `vite.config.ts` (importando `defineConfig` de `vitest/config`, que es el mismo de Vite
  más la clave `test`) para que tests y aplicación compartan un solo pipeline. Los ficheros
  van junto a lo que prueban, como `*.test.ts(x)`, igual que en el backend. **Sin
  `globals: true`**: cada test importa `describe`/`it`/`expect`, con lo que nada aparece por
  arte de magia y el tsconfig no necesita declarar tipos globales — a cambio, la limpieza
  automática de Testing Library hay que engancharla a mano en `src/test/setup.ts`, que es
  justo lo que hace ese fichero.
- **Estado de cliente**: los stores de Zustand viven en `src/features/<área>/`, uno por área
  (`features/ui/uiStore.ts` es el primero, todavía de ejemplo). Guardan **solo** lo que
  decide el usuario mientras navega: un menú desplegado, un filtro elegido, el paso de un
  asistente. Nada que venga de la API entra en un store — eso es de TanStack Query, y
  duplicarlo es cómo se queda obsoleto sin que nadie se entere. Los componentes leen con un
  selector por dato (`useUiStore((state) => state.isMobileMenuOpen)`), no el store entero,
  para no re-renderizar con cada cambio ajeno.
- **Estado de servidor**: `src/lib/queryClient.ts` construye el `QueryClient` con las
  opciones por defecto de toda la aplicación, y `main.tsx` lo cuelga de un
  `QueryClientProvider`. Se instancia a nivel de módulo, no dentro de un componente: la
  caché vive en esa instancia y recrearla en cada render la tiraría entera. Un `staleTime`
  de 30 s, que cada consulta sobreescribe si lo suyo es más volátil, y un `retry` que
  respeta la marca `retryable` de los errores: **no se reintenta lo que no va a cambiar**
  — un 409 de hueco ya reservado, un 429 del rate limiter (donde insistir empeora las
  cosas) ni una respuesta que incumple su schema — mientras que los fallos de red y los
  5xx se reintentan dos veces, porque el arranque en frío de Render (~40 s) hace caer la
  primera petición de una visita con el servicio sano. La comprobación es **estructural**,
  no un `instanceof`: `lib/` no puede importar de `api/`, así que la capa de servicios
  marca sus errores y aquí solo se lee la marca.
- **Capa de API**: `src/api/http.ts` envuelve el `fetch` nativo — nada de axios, que no
  aportaría nada sobre lo que TanStack Query ya resuelve y sería una dependencia más que
  auditar. Cada endpoint es una función (`getAppointmentTypes()`,
  `getAvailability(params)`) que declara su **schema de Zod**, y ese schema es la única
  fuente: el tipo sale de `z.infer`, nunca se escribe una interfaz gemela al lado. La
  validación en runtime no es ceremonia — los tipos de TypeScript se borran al compilar, y
  sin ella un campo renombrado en el backend viaja sin ruido hasta reventar tres
  componentes más abajo; con ella falla en el borde, como `ApiContractError`, diciendo qué
  endpoint y qué campo. Los errores de negocio del backend (`{code, detail}` de
  `app/core/errors.py`) llegan como `ApiError`, con su `status`. La frontera snake_case →
  camelCase se cruza **una sola vez**, en el `transform` de cada schema. Los instantes se
  convierten a `Date` ahí mismo (es el borde donde este proyecto convierte tiempo), pero
  el día natural se queda en texto `YYYY-MM-DD`: no es un instante sino la etiqueta del
  día en la zona del dueño, y pasarlo por `Date` lo clavaría a medianoche UTC y le pintaría
  el día anterior a quien reserve desde Canarias o Argentina.
- `docker-compose.yml` (raíz del repo) une `backend` + `postgres` solo para desarrollo local
  — producción usa Render + Neon, no este compose.

## Convenciones

- **Comentarios, docstrings y documentación interna en español** (ver la sección "Idioma").
- Identificadores del código, nombres de rama y mensajes de commit en **inglés**. Textos de
  interfaz y emails en **español**.
- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:` — mensajes
  de commit de una sola línea.
- Type hints en todo el Python. TypeScript estricto en el frontend.

## Flujo de git

- Trunk-based. `main` está protegida — GitHub rechaza los push directos.
- Ramas: `feature/<nombre>`, `fix/<nombre>`, `chore/<nombre>`, `docs/<nombre>`,
  `test/<nombre>`, `refactor/<nombre>` — salidas de `main`, mismos tipos que los de
  Conventional Commits (ver "Convenciones").
- Todo cambio pasa por un PR. Solo squash merge.

## Decisiones de arquitectura

No propongas ni añadas infraestructura más allá de esto sin que te lo pidan:

- **Nada** de Redis, brokers de mensajes, Kubernetes, service workers ni microservicios.
- La reserva pública **no tiene login**. El acceso a una reserva es por token opaco
  (`secrets.token_urlsafe(32)`), nunca por un ID secuencial — así se evita el IDOR.
- El panel de administración está autenticado: un solo rol, aplicado con una dependencia
  reutilizable `require_role` vía `Depends()`. El frontend solo gestiona la visibilidad de
  la interfaz.
- Migraciones con Alembic, aplicadas al desplegar — nunca al arrancar la aplicación.
- Todas las marcas de tiempo se guardan en **UTC**; la conversión ocurre en los bordes.
- El backend corre en el plan gratuito de Render — el arranque en frío (~40 s) se gestiona
  en la interfaz, no pagando.

## Seguridad

Este es un **repositorio público**.

- Nunca commitees secretos. Toda la configuración va por variables de entorno. `.env` está
  en `.gitignore`; `.env.example` se commitea con valores de ejemplo.
- Escaneo de secretos: `gitleaks` corre en cada PR
  (`.github/workflows/secret-scan.yml`) sobre el historial **completo** de git, así que un
  secreto que llegó a entrar sigue tumbando la CI hasta que se purga del historial — no
  basta con borrarlo en un commit posterior. Usa la CLI MIT desde una imagen fijada por
  digest en vez de `gitleaks-action`, que exige licencia de pago para repositorios de una
  organización. Dependabot no sigue ese digest; súbelo a mano.
- SAST: CodeQL analiza el código Python y TypeScript en cada PR, en los push a `main` y
  semanalmente (`.github/workflows/codeql.yml`), publicando en la pestaña Security. A
  propósito la configuración *avanzada* — un workflow commiteado — y no la de un clic, que
  vive en los ajustes del repositorio y por tanto no la heredaría una app generada desde
  esta plantilla. No actives nunca las dos: entran en conflicto. Un lenguaje solo entra en
  la matriz cuando ya hay ficheros suyos que analizar: CodeQL tumba la ejecución entera si
  uno de los configurados no tiene nada que extraer.
- Escaneo de dependencias: `pip-audit` gobierna cada PR de backend y `npm audit
  --audit-level=high` cada PR de frontend. Dependabot propone las actualizaciones; estos
  jobs son lo que impide que un aviso se ignore mientras esa cadencia semanal va llegando.
- CORS: lista blanca de orígenes explícita por entorno. Nunca `*` combinado con
  credenciales. `Settings.cors_origins` es una lista vacía por defecto, así que un entorno
  que se olvide de `CORS_ORIGINS` no permite nada en vez de caer al localhost de un
  desarrollador. Los entornos locales lo declaran en `.env` / `docker-compose.yml`.
- Sentry: `send_default_pii=False`, más un gancho `before_send` — `scrub_event` en
  `app/core/observability.py` — que recorre el evento entero redactando los valores que
  cuelgan de claves sensibles y cualquier email o teléfono español que aparezca en texto
  libre. `send_default_pii=False` solo impide que Sentry recoja PII por su cuenta; no hace
  nada con la PII que le pasa la aplicación en un mensaje de log o en una variable local
  capturada, que es donde se escapa de verdad. Los eventos siempre se limpian, nunca se
  descartan.
- Rate limiting en los endpoints públicos (creación de reservas).
- Cabeceras de seguridad: HSTS, X-Content-Type-Options, X-Frame-Options, CSP básica.

## Restricciones de stack

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL. Ruff para lint y formato, mypy para
  tipos, uv para gestionar dependencias (`uv.lock` se commitea).
- Frontend: React + Vite + TypeScript, Zustand (estado global), TanStack Query (estado de
  servidor).
- Tests: pytest (backend), Vitest (frontend). Los tests de lógica de negocio se escriben
  junto a la lógica, no se aplazan a una fase posterior.
- CI/CD: los workflows están en `.github/workflows/` y corren automáticamente en cada PR.
