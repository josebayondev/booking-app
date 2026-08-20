# Starting a new project from this template

This repository is a GitHub template. Everything that cannot live in code — service names,
credentials, endpoints, and the GitHub settings a template does not carry — is listed here.

Work through it top to bottom, then **delete this file**. It is the last commit of the setup,
not part of the project.

---

## 1. Rename the project

Four strings carry the old project's identity. Find every occurrence first:

```bash
grep -rn "booking-app-backend\|booking_app\|booking-backend\|Booking App API" \
  --exclude-dir=.git --exclude-dir=.venv --exclude=uv.lock --exclude=TEMPLATE.md .
```

| String | Where | What it is |
| --- | --- | --- |
| `booking-app-backend` | `backend/pyproject.toml` | Python package name |
| `Booking App API` | `backend/app/core/config.py`, `backend/.env.example` | `PROJECT_NAME`, the title FastAPI shows in `/docs` |
| `booking_app` | `docker-compose.yml`, `backend/.env.example`, `backend/app/core/config.py`, `backend/tests/conftest.py`, `.github/workflows/backend-ci.yml` | Local/CI database name |
| `booking-backend` | `CLAUDE.md`, `.github/workflows/backend-ci.yml` | Docker image tag |

A single pass does all of it (this is GNU sed; on macOS use `sed -i ''`):

```bash
grep -rl "booking-app-backend\|booking_app\|booking-backend\|Booking App API" \
  --exclude-dir=.git --exclude-dir=.venv --exclude=uv.lock --exclude=TEMPLATE.md . \
| xargs sed -i \
  -e 's/booking-app-backend/<your-app>-backend/g' \
  -e 's/booking-backend/<your-app>-backend/g' \
  -e 's/booking_app/<your_app>/g' \
  -e 's/Booking App API/<Your App> API/g'
```

Then re-run `grep` to confirm nothing is left, and `cd backend && uv sync --extra dev` so the
lockfile picks up the new package name.

Do **not** rename `alembic/versions/3168153d1c43_baseline.py` or its revision id. It is an
empty baseline and the new project builds its own migrations on top of it.

## 2. Create the external services

| Service | What to create | Notes |
| --- | --- | --- |
| **Neon** | A project with a `production` branch and a `dev` branch | Pick the region **before** creating anything else; moving it later means recreating the project |
| **Render** | A Web Service, Docker runtime, autodeploy from `main` | Same region as Neon, or every query pays a transatlantic round trip |
| **Vercel** | A project pointing at `frontend/` | Only once the frontend scaffold exists |
| **Sentry** | A project, backend platform | Optional; leaving `SENTRY_DSN` empty disables it cleanly |

Then set the variables. Nothing here belongs in the repository:

| Where | Variable | Value |
| --- | --- | --- |
| Render → Environment | `ENVIRONMENT` | `production` (or `preview`) |
| Render → Environment | `DATABASE_URL` | Neon `production` connection string |
| Render → Environment | `CORS_ORIGINS` | The deployed frontend origin. Comma-separated for several; **never** `*` |
| Render → Environment | `SENTRY_DSN` | From Sentry, or leave unset |
| GitHub → Secrets → Actions | `DATABASE_URL_PRODUCTION` | Neon `production` connection string, used by `migrate-production.yml` |
| Local | `backend/.env` | `cp backend/.env.example backend/.env` and point `DATABASE_URL` at local Postgres |

Until `DATABASE_URL_PRODUCTION` exists, the migrations workflow finishes green and logs a
notice saying it skipped. That is deliberate — see the guard step in
`.github/workflows/migrate-production.yml`.

## 3. GitHub settings the template does not carry

A template copies files. It does not copy repository configuration, and this is the part that
silently goes missing.

**Branch ruleset on `main`** — require a pull request, block deletion and force pushes, and
require these status checks by their exact names:

```
ruff   mypy   pytest   docker-build   migrations   pip-audit   gitleaks
CodeQL   analyze (python)
lint   typecheck   build   audit
```

The last four are the frontend jobs. They report `skipped` while `frontend/package.json` does
not exist, which counts as passing, so adding them now costs nothing and means you will not
have to remember once the scaffold lands.

**Secret scanning and push protection** — Settings → Advanced Security. Free on public
repositories. `gitleaks` in CI covers the history; push protection covers the moment before a
secret is ever pushed. They are complementary, keep both.

> **If the new repository is private:** `codeql.yml` will fail. Code scanning is free only on
> public repositories; on a private one it needs paid GitHub Code Security. Either pay for it,
> or delete `.github/workflows/codeql.yml` and drop `CodeQL` and `analyze (python)` from the
> required checks. Do not leave the workflow in place and failing.

## 4. Rewrite the documentation

These describe the old project and are wrong for yours from the first commit:

- **`README.md`** — title, description, and the Environments table. Remove the pointer to this
  file at the top.
- **`CLAUDE.md`** — rewrite `## Project` and `## Architecture decisions`. Everything else
  (commands, architecture of `config.py` / `db.py` / middleware / tests, security, git
  workflow, stack constraints) applies unchanged and is the reason this template exists.
- **`.claude/README.md`** — the closing paragraph refers to this project's ClickUp lists.

## 5. Known gaps

Inherited as-is. None of them breaks the build; all of them are work you still owe:

- **No rate limiting.** `CLAUDE.md` lists it under Security, but it is not implemented — it
  needs a real public endpoint to be worth anything.
- **No `require_role`.** The admin-panel authorisation dependency described in
  `## Architecture decisions` does not exist yet. It needs a user model, password hashing, a
  login endpoint and a migration.
- **`frontend/` is an empty placeholder.** Its four CI jobs (`lint`, `typecheck`, `build`,
  `audit`) are written but have **never executed** — the `changes` guard in `frontend-ci.yml`
  keeps them skipped until `frontend/package.json` exists. Review the first frontend PR
  carefully: those jobs will be running for the very first time.

---

## Done

```bash
git rm TEMPLATE.md
```

Then check the setup end to end: `docker compose up --build` should serve
`http://localhost:8000/health`, and a throwaway pull request should turn every required check
green without any code changes.
