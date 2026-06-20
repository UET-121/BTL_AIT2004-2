# License Plate Recognition

A Docker-based monorepo for Brazilian license plate recognition with a FastAPI backend, Celery worker, PostgreSQL, Redis, and a React/Vite frontend.

## Table of contents

- [License Plate Recognition](#license-plate-recognition)
  - [Table of contents](#table-of-contents)
  - [Overview](#overview)
  - [Key features](#key-features)
  - [Architecture](#architecture)
    - [Services in `docker-compose.yml`](#services-in-docker-composeyml)
  - [Tech stack](#tech-stack)
  - [Repository structure](#repository-structure)
  - [Getting started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Environment configuration](#environment-configuration)
    - [Run with Docker](#run-with-docker)
    - [Run services locally](#run-services-locally)
  - [Backend](#backend)
    - [API endpoints](#api-endpoints)
    - [Worker pipeline](#worker-pipeline)
  - [Frontend](#frontend)
  - [Tests](#tests)
  - [Plan docs](#plan-docs)
  - [Known gaps / TODO](#known-gaps--todo)
  - [Notes](#notes)

---

## Overview

This project is a license plate recognition system built as a full-stack monorepo. It provides an API for image upload, async recognition processing, and a frontend UI for viewing recognition requests.

The backend is implemented in `apps/api`, while the frontend lives in `frontend`.

## Key features

- FastAPI backend with `/health` and `/api/v1/recognition` endpoints
- Async processing via Celery and Redis
- PostgreSQL metadata storage
- Local file storage for uploaded images
- React/Vite frontend UI served on port `5173`
- Docker Compose orchestration for the full stack

## Architecture

```text
Client (browser) → Frontend (Vite/React)
        ↓
  Upload image → FastAPI API
        ↓
  PostgreSQL metadata + local upload storage
        ↓
  Celery worker (async recognition task)
        ↓
  ML pipeline: detection → OCR → validation → status update
```

### Services in `docker-compose.yml`

| Service | Port | Purpose |
|---|---|---|
| `db` | `5433:5432` | PostgreSQL database |
| `redis` | `6380:6379` | Celery broker / cache |
| `api` | `8000:8000` | FastAPI backend |
| `worker` | n/a | Celery worker |
| `frontend` | `5173:5173` | React/Vite frontend |

## Tech stack

- Backend: Python, FastAPI, SQLAlchemy, Alembic
- Async: Celery, Redis
- Database: PostgreSQL
- Storage: local disk uploads
- Frontend: React, Vite, TypeScript
- Containerization: Docker, Docker Compose

## Repository structure

```text
.
├── apps/api/             # FastAPI backend, Celery worker, database migration
│   ├── app/
│   │   ├── api/          # FastAPI route definitions
│   │   ├── models/       # Pydantic schemas
│   │   ├── services/     # Storage + ML service factories
│   │   ├── shared/       # Config + database session setup
│   │   ├── worker/       # Celery app + async task
│   │   └── main.py       # FastAPI application entry point
│   ├── Dockerfile
│   ├── Makefile
│   ├── migrations/
│   ├── requirements.txt
│   └── README.md
├── frontend/             # React/Vite frontend application
│   ├── src/
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── plan/                 # Sprint planning and design documents
├── docker-compose.yml
├── .env.example
└── README.md
```

## Getting started

### Prerequisites

- Docker 24+
- Docker Compose v2+
- Node.js 18+ (frontend local development)
- Python 3.11+ (backend local development)

### Environment configuration

Copy the root env template and update values as needed:

```bash
cp .env.example .env
```

The root `.env.example` contains database and service defaults. The backend also uses `apps/api/.env.example` for local development.

### Run with Docker

Start the full stack:

```bash
docker compose up -d --build
```

Verify services:

```bash
docker compose ps
curl http://localhost:8000/health
```

### Run services locally

Backend from `apps/api`:

```bash
cd apps/api
cp .env.example .env
pip install -r requirements.txt
make migrate
make api
```

Worker in a second terminal:

```bash
cd apps/api
make worker
```

Frontend from `frontend`:

```bash
cd frontend
npm install
npm run dev
```

Access the app at `http://localhost:5173` and the backend at `http://localhost:8000`.

## Backend

The backend application is in `apps/api`.

- Entry point: `apps/api/app/main.py`
- API routes: `apps/api/app/api/routes.py`
- Pydantic schemas: `apps/api/app/models/schemas.py`
- Config: `apps/api/app/shared/config.py`
- Database session: `apps/api/app/shared/database.py`
- Storage abstraction: `apps/api/app/services/storage.py`
- Celery worker: `apps/api/app/worker/celery_app.py`
- Recognition task: `apps/api/app/worker/tasks.py`

### API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check for DB and Redis |
| POST | `/api/v1/recognition` | Upload a JPEG/PNG image and queue recognition |
| GET | `/api/v1/recognition/{request_id}` | Retrieve request result |
| GET | `/api/v1/recognition` | Paginated list of recognition requests |
| POST | `/api/v1/recognition/{request_id}/reprocess` | Reprocess requests in `FAILED` or `NEEDS_REVIEW` state |

### Worker pipeline

When a request is created, a Celery task is queued:

- `process_plate_recognition.delay(request_id)`
- Worker loads the record and marks it `PENDING`
- The recognition service performs detection, OCR, validation, and scoring
- Result fields are written back to the database
- The request may become `COMPLETED`, `NEEDS_REVIEW`, or `FAILED`

## Frontend

The frontend lives in `frontend` and is served by Vite on `5173`.

- Config: `frontend/vite.config.ts`
- Environment: `frontend/.env.example`
- Dockerfile: `frontend/Dockerfile`

The frontend proxy is configured to forward `/api` and `/uploads` to the backend.

## Tests

Backend tests are available under `apps/api/tests`.

Run tests:

```bash
cd apps/api
pytest tests/ -v --tb=short
```

## Plan docs

Project plans and track documentation are stored in `plan/`.

Key plan readmes:

- `plan/README.md`
- `plan/backend/README.md`
- `plan/frontend/README.md`
- `plan/devops/README.md`

## Known gaps / TODO

- `apps/api/app/models/recognition.py` is referenced in plan docs but not present in the current live backend source
- Advanced ML model artifacts and recognition logic are not fully wired in the current backend source tree
- Frontend UX details are described in `plan/frontend/README.md` and may require additional implementation work

---

## Notes

This repository is a redesign of a license plate recognition system with a monorepo structure and a focus on fast local development via Docker Compose.
