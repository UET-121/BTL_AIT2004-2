# Target Architecture — License Plate Recognition

## System Overview

```mermaid
flowchart TB
    subgraph client [Frontend apps/web]
        UI[React SPA]
        Crop[Cropper]
    end

    subgraph gateway [nginx port 80]
        Proxy[API Proxy]
    end

    subgraph backend [Backend apps/api]
        API[FastAPI :8000]
        Worker[Celery Worker]
        Recog[RecognitionService]
    end

    subgraph ml [AI Pipeline]
        Detect[Plate Detector]
        Pre[Preprocessing]
        OCR[EasyOCR]
        Val[BR Validator]
    end

    subgraph infra [Docker Compose]
        PG[(PostgreSQL)]
        Redis[(Redis)]
        Vol[uploads volume]
    end

    UI --> Crop --> Proxy --> API
    Proxy --> API
    API --> PG
    API --> Redis
    API --> Vol
    Redis --> Worker
    Worker --> Recog
    Recog --> Detect --> Pre --> OCR --> Val
    Worker --> PG
```

## Monorepo Layout (Target)

```
license-plate-recognition/
├── apps/
│   ├── api/                    # FastAPI + Celery + ML services
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── api/routes.py
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   │   ├── detection/
│   │   │   │   ├── ocr/
│   │   │   │   ├── preprocessing/
│   │   │   │   ├── validation/
│   │   │   │   ├── recognition.py
│   │   │   │   └── storage.py
│   │   │   ├── worker/
│   │   │   └── shared/
│   │   ├── migrations/
│   │   ├── Dockerfile
│   │   ├── Makefile
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── web/                    # React/Vite SPA
│       ├── src/
│       ├── Dockerfile
│       └── nginx.conf
├── models/                     # DVC-tracked weights
│   ├── detection/
│   ├── onnx/
│   └── release/
├── datasets/                   # Training/eval data (gitignored raw)
├── notebooks/                  # ML exploration
├── scripts/                    # CI, smoke test, backup
├── plan/                       # Agile redesign docs (this folder)
├── data/                       # Docker volumes (gitignored)
├── docker-compose.yml
├── docker-compose.dev.yml
├── Makefile                    # Root wrapper
└── .env.example
```

## Recognition Pipeline Flow

```mermaid
sequenceDiagram
    participant User
    participant Web as Frontend
    participant API as FastAPI
    participant Redis
    participant Worker as Celery Worker
    participant ML as RecognitionService
    participant DB as PostgreSQL

    User->>Web: Upload image (optional crop)
    Web->>API: POST /api/v1/recognition
    API->>DB: INSERT status=NOT_STARTED
    API->>Redis: enqueue task
    API-->>Web: 200 {request_id, status}

    Redis->>Worker: process_plate_recognition
    Worker->>DB: UPDATE status=PENDING
    Worker->>ML: recognize(image_path)

    ML->>ML: Detect plate region
    ML->>ML: Preprocess (quality/deblur/enhance)
    ML->>ML: EasyOCR
    ML->>ML: BR format validation
    ML->>ML: Confidence scoring

    alt confidence >= AUTO_ACCEPT
        Worker->>DB: status=COMPLETED
    else confidence < NEEDS_REVIEW
        Worker->>DB: status=NEEDS_REVIEW
    else all retries failed
        Worker->>DB: status=FAILED
    end

    Web->>API: GET /api/v1/recognition/{id} (poll)
    API-->>Web: Full response + metadata
```

## Component Responsibilities

| Component | Owner | Responsibility |
|-----------|-------|----------------|
| `apps/web` | Frontend | Upload UI, crop, list, detail, polling, review UX |
| `apps/api/app/api` | Backend | REST endpoints, validation, error handling |
| `apps/api/app/worker` | Backend | Celery tasks, status lifecycle |
| `apps/api/app/services/recognition.py` | Backend + AI | Orchestrate ML pipeline |
| `apps/api/app/services/detection/` | AI | YOLO / ONNX plate detection |
| `apps/api/app/services/ocr/` | AI | EasyOCR integration |
| `apps/api/app/services/preprocessing/` | AI | Image enhancement pipeline |
| `apps/api/app/services/validation/` | AI | Brazilian plate rules |
| `docker-compose.yml` | DevOps | Service orchestration |
| `models/` | AI + DevOps | Versioned weights via DVC |

## Data Model (Target)

### `recognition_requests` table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID PK | Request identifier |
| `image_url` | VARCHAR | Path/URL to stored image |
| `plate_number` | VARCHAR NULL | Recognized plate text |
| `status` | ENUM | NOT_STARTED, PENDING, COMPLETED, NEEDS_REVIEW, FAILED |
| `error_message` | TEXT NULL | Error detail if FAILED |
| `confidence_score` | FLOAT NULL | Combined confidence 0–1 |
| `detection_confidence` | FLOAT NULL | Detector confidence |
| `ocr_confidence` | FLOAT NULL | OCR confidence |
| `needs_review` | BOOLEAN | Auto-flag for manual review |
| `bounding_box` | JSON NULL | `{x, y, width, height}` |
| `plate_region` | VARCHAR NULL | e.g. `BR` |
| `created_at` | TIMESTAMP | Created |
| `updated_at` | TIMESTAMP | Last updated |

## API Surface (Summary)

Full contract: [`05-api-contracts.md`](05-api-contracts.md)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (+ extended deps in Sprint 2) |
| POST | `/api/v1/recognition` | Upload image, queue task |
| GET | `/api/v1/recognition/{id}` | Get request detail |
| GET | `/api/v1/recognition` | Paginated list |
| POST | `/api/v1/recognition/{id}/reprocess` | Re-queue FAILED/NEEDS_REVIEW |
| GET | `/uploads/{filename}` | Static image serve |

## Environment Profiles

| Profile | Command | Use case |
|---------|---------|----------|
| `infra-only` | `docker compose up db redis` | Local dev, API/worker chạy ngoài container |
| `dev` | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` | Hot reload |
| `prod-like` | `docker compose --profile prod up` | Pre-release validation |

## Integration Points (Cross-team)

| Interface | Producer | Consumer | Contract |
|-----------|----------|----------|----------|
| REST API | Backend | Frontend | OpenAPI `/docs` |
| ML output schema | AI | Backend | JSON spec in Sprint 3 AI |
| Model artifacts | AI | DevOps | `models/release/v1.0/` |
| Env variables | DevOps | All | [`06-env-variables.md`](06-env-variables.md) |
| Docker services | DevOps | All | `docker-compose.yml` healthchecks |

## Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Availability (local) | 5 services healthy after `docker compose up` |
| Latency p95 | Upload → COMPLETED < 30s |
| Scalability (local) | 10 concurrent uploads (locust spike) |
| Observability | Structured JSON logs, request ID propagation |
| Security (local) | No secrets in git, `.env` gitignored |
| Maintainability | Pre-commit hooks, CI script, ≥ 70% backend coverage |
