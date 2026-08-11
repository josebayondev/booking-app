# booking-app

Appointment booking system — FastAPI, React, PostgreSQL.

Public booking without login (access via opaque token) and an admin panel behind authentication.

## Stack

| Layer     | Tech                                              |
| --------- | ------------------------------------------------- |
| Frontend  | React + Vite + TypeScript → Vercel                |
| Backend   | FastAPI + SQLAlchemy + Alembic, Docker → Render   |
| Database  | PostgreSQL (Neon)                                 |
| CI        | GitHub Actions                                    |
| Errors    | Sentry                                            |

## Structure

```
booking-app/
├── backend/            FastAPI application
├── frontend/           React + Vite application
└── .github/workflows/  CI pipelines
```

## Getting started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your own values
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Local database

```bash
docker compose up -d
```

## Database migrations

Migrations are managed with Alembic. The migration file is committed and reviewed
in the PR; it is applied automatically on deploy, never at application startup.

```bash
alembic revision --autogenerate -m "description"   # generate (always review the output)
alembic upgrade head                               # apply
alembic downgrade -1                               # roll back one revision
```

Test migrations against a Neon branch before they reach production.

## Branching

Trunk-based. `main` is always deployable.

- Branch off `main`: `git checkout -b feature/<name>`
- Open a PR against `main` — direct pushes are blocked
- CI must pass before merging
- Squash merge; the remote branch is deleted automatically
- Rebase onto `main` instead of merging it in, to keep history linear

Prefixes: `feature/`, `fix/`, `chore/`, `docs/`

## Conventions

- Code, branch names and commit messages in **English**
- User-facing UI and emails in **Spanish**
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`
- No secrets in the repository — all configuration through environment variables

## Environments

| Environment | Frontend        | Backend        | Database    |
| ----------- | --------------- | -------------- | ----------- |
| Local       | localhost:5173  | localhost:8000 | Docker      |
| Production  | Vercel          | Render         | Neon (main) |