# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communicating with Claude Code

Always respond to the developer in **Spanish**, regardless of the language of his message.
This is about chat responses only — it does not change the "Conventions" section below
(code, branch names and commit messages stay in English).

## Project

Appointment booking system. Monorepo: `backend/` (FastAPI + SQLAlchemy + Alembic) and
`frontend/` (React + Vite + TypeScript). Public booking has no login; the admin panel is
authenticated. Backend deploys to Render, frontend to Vercel, database is Neon Postgres.

`frontend/` is currently an empty placeholder (no scaffold yet). `backend/` has the app
skeleton (`FastAPI` instance, `/health`, settings, Docker) plus a CI workflow
(`.github/workflows/backend-ci.yml`), but no SQLAlchemy models or Alembic setup yet —
those land in later FEATs. There is no frontend CI yet either (FEAT 4.2).

## Commands you must NOT run

The developer runs these himself. Write the code and the files, then stop and tell him
what to run — never execute them yourself:

- `git add`, `git commit`, `git push`, `git merge`, `git rebase`, `git reset`
- **Any `alembic` command**, including `revision`, `revision --autogenerate`, `upgrade`
  and `downgrade`. Do not create or edit migration files under `alembic/versions/` either
  — the developer generates and reviews every migration himself.
- Any command that deploys, or that writes to a remote database

You may read git state (`git status`, `git diff`, `git log`).

When a change requires a migration, say so explicitly and describe what the migration
should contain — then stop.

## Backend commands

Run from `backend/`:

Dependencies are managed with **uv**, and `uv.lock` is committed — it pins every
transitive dependency, so local, CI and the Docker image all install identical versions.
Install uv with `brew install uv` (or `pip install uv` inside the venv).

```bash
uv sync --extra dev             # create/update .venv from uv.lock (exact versions)
uv run uvicorn app.main:app --reload   # dev server: http://localhost:8000, docs at /docs
uv run ruff check .             # lint
uv run ruff format .            # format
uv run mypy app                 # type check (strict mode)
uv run pytest                   # tests (backend/tests/ — one smoke test so far, /health)
```

Changing dependencies — always commit the resulting `uv.lock` in the same PR:

```bash
uv add <package>                # add a runtime dependency (updates pyproject + lock)
uv add --optional dev <package> # add a dev dependency
uv lock --upgrade               # refresh every pin to the latest allowed version
```

Note that `uv sync` makes the venv match the lock exactly, so it removes anything not
in it. CI and Docker use `uv sync --frozen`, which fails instead of re-resolving when
`uv.lock` is out of sync with `pyproject.toml`.

## Frontend commands

Run from `frontend/` once the scaffold exists:

```bash
npm install
cp .env.example .env
npm run dev
```

## Docker / local environment

```bash
docker compose up --build       # from repo root: backend + local postgres together
docker build -t booking-backend ./backend   # backend image alone
```

Local Postgres credentials in `docker-compose.yml` (`postgres`/`postgres`/`booking_app`)
are fixed dev-only values, not secrets — they never touch real data and don't apply to
Neon (staging/production).

## Architecture

- **Settings**: `app/core/config.py` — a `pydantic-settings` `Settings` class, cached via
  `get_settings()` (`lru_cache`), reads `.env`. Add new env-driven config here.
- **Startup / DB check**: `app/main.py` registers a `lifespan` context manager that calls
  `check_db_connection()` (`app/core/db.py`) — a minimal raw `psycopg` `SELECT 1`, no ORM.
  This is a deliberate placeholder standing in for the real SQLAlchemy engine, session
  factory and `get_db()` dependency, which are still to-do; expect `app/core/db.py` to be
  replaced when that lands. Startup fails fast (raises) if the DB is unreachable.
- **Routing**: routers live under `app/api/` (e.g. `health.py`) and are registered on the
  `FastAPI` app in `main.py` via `app.include_router(...)`.
- `app/models/` and `app/schemas/` are empty scaffolding for SQLAlchemy models and
  Pydantic schemas respectively.
- **Docker build**: `backend/Dockerfile` is a two-stage build — `builder` installs the
  locked dependencies into a venv at `/opt/venv` (via `uv sync --frozen
  --no-install-project`, so only `pyproject.toml` + `uv.lock` are copied and dependency
  installs aren't invalidated by every code change); `runtime` copies that venv plus the
  `app/` source straight from the build context. The project itself is deliberately never
  installed as a package — `app` is importable because it sits in the working directory.
  Runs as a non-root user, and honors `$PORT` (falling back to 8000) for Render, whose CMD
  uses shell form so the env var expands.
- **Pinning**: both stages pin `python:3.13-slim` by digest, and the uv binary comes from
  a digest-pinned `ghcr.io/astral-sh/uv` image — same reasoning as pinning GitHub Actions
  by SHA. Dependabot (`.github/dependabot.yml`) keeps the lockfile, the image digests and
  the action SHAs up to date.
- `docker-compose.yml` (repo root) wires `backend` + `postgres` together for local dev
  only — production uses Render + Neon instead, not this compose file.

## Conventions

- Code, branch names and commit messages in **English**. UI text and emails in **Spanish**.
- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:` — keep
  commit messages to a single line.
- Type hints everywhere in Python. Strict TypeScript in the frontend.

## Git workflow

- Trunk-based. `main` is protected — direct pushes are rejected by GitHub.
- Branches: `feature/<name>`, `fix/<name>`, `chore/<name>`, branched off `main`.
- All changes go through a PR. Squash merge only.

## Architecture decisions

Do not propose or add infrastructure beyond this without being asked:

- **No** Redis, message broker, Kubernetes, service workers, or microservices.
- Public booking has **no login**. Access to a booking is via an opaque token
  (`secrets.token_urlsafe(32)`), never a sequential ID — this prevents IDOR.
- Admin panel is authenticated: single role, enforced with a reusable `require_role`
  dependency via `Depends()`. Frontend handles UI visibility only.
- Migrations with Alembic, applied on deploy — never at application startup.
- All timestamps stored in **UTC**; convert at the boundary.
- Backend runs on Render free tier — cold start (~40s) is handled in the UI, not by paying.

## Security

This is a **public repository**.

- Never commit secrets. All configuration through environment variables.
  `.env` is gitignored; `.env.example` is committed with placeholder values.
- CORS: explicit origin allow-list per environment. Never `*` combined with credentials.
- Sentry: `send_default_pii=False`, scrub sensitive fields.
- Rate limiting on public endpoints (booking creation).
- Security headers: HSTS, X-Content-Type-Options, X-Frame-Options, basic CSP.

## Stack constraints

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL. Ruff for lint and format, mypy for
  types, uv for dependency management (`uv.lock` is committed).
- Frontend: React + Vite + TypeScript, Zustand (global state), TanStack Query (server state).
- Tests: pytest (backend), Vitest (frontend). Business logic tests are written alongside
  the logic, not deferred to a later phase.
