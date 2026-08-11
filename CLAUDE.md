# booking-app

Appointment booking system. Monorepo: `backend/` (FastAPI + SQLAlchemy + Alembic) and
`frontend/` (React + Vite + TypeScript).

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

## Conventions

- Code, branch names and commit messages in **English**. UI text and emails in **Spanish**.
- Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`
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

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL. Ruff for lint and format, mypy for types.
- Frontend: React + Vite + TypeScript, Zustand (global state), TanStack Query (server state).
- Tests: pytest (backend), Vitest (frontend). Business logic tests are written alongside
  the logic, not deferred to a later phase.