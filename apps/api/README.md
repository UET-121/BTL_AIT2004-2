# License Plate Recognition — Backend API

FastAPI + Celery + PostgreSQL backend for Brazilian license plate recognition.

## Quick start

```bash
# From repo root — start infrastructure
docker compose up -d

# Backend setup
cd apps/api
cp .env.example .env
pip install -r requirements.txt
make migrate

# Terminal 1 — API
make api

# Terminal 2 — Celery worker
make worker
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (DB + Redis) |
| POST | `/api/v1/recognition` | Upload image |
| GET | `/api/v1/recognition/{id}` | Get request |
| GET | `/api/v1/recognition` | List (paginated) |
| POST | `/api/v1/recognition/{id}/reprocess` | Reprocess FAILED/NEEDS_REVIEW |

OpenAPI: http://localhost:8000/docs

## ML pipeline (shared with AI Engineer)

```
Image → Detection (YOLO) → Preprocessing → EasyOCR → BR Validation → Confidence
```

Key paths:
- `app/services/recognition.py` — orchestrator
- `app/services/detection/` — plate detection
- `app/services/ocr/` — EasyOCR
- `app/services/preprocessing/` — image enhancement
- `app/services/validation/` — Brazilian plate rules

## Tests

```bash
# Create test DB first
docker exec -it <postgres_container> psql -U postgres -c "CREATE DATABASE plate_recognition_test;"

make test
```
