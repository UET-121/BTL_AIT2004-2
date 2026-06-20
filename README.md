# License Plate Recognition

Brazilian license plate recognition system - monorepo redesign.

## Structure

```text
apps/api/     FastAPI backend + ML pipeline + Celery worker
frontend/     React/Vite admin SPA
plan/         Agile sprint plans (4 tracks)
docker-compose.yml   PostgreSQL + Redis + frontend
```

## Quick start

```bash
docker compose up -d
cd apps/api && cp .env.example .env && pip install -r requirements.txt
make migrate && make api

cd ../../frontend
npm install
npm run dev
```

See [frontend/README.md](frontend/README.md) for the frontend runbook.
