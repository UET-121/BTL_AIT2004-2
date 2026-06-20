# Environment Variables — Master Reference

Tổng hợp biến môi trường cho tất cả nhánh. Nguồn: [`apps/api/.env.example`](../../apps/api/.env.example) + frontend + DevOps additions.

**Quy tắc:**

- File `.env` không commit — chỉ `.env.example`
- Mọi biến mới phải cập nhật file này + `.env.example` tương ứng
- Docker Compose đọc từ root `.env.example` hoặc `.env`

---

## Backend (`apps/api/.env`)

### Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | Async PostgreSQL URL. Format: `postgresql+asyncpg://user:pass@host:5432/dbname` |
| | | `postgresql+asyncpg://postgres:postgres@localhost:5432/plate_recognition` | Local dev |
| | | `postgresql+asyncpg://postgres:postgres@db:5432/plate_recognition` | Docker compose |

### Redis / Celery

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | `redis://localhost:6379/0` | Celery broker URL |
| | | `redis://redis:6379/0` | Docker compose |

### Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STORAGE_TYPE` | Yes | `local` | `local`, `minio`, `s3`, `supabase` |
| `UPLOAD_DIR` | Yes | `uploads` | Local upload directory |
| | | `/app/uploads` | Docker container path |

### AWS S3 (optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | If S3 | — | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | If S3 | — | AWS secret key |
| `AWS_BUCKET_NAME` | If S3 | — | S3 bucket name |
| `AWS_REGION` | If S3 | `us-east-1` | AWS region |

### Supabase (optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | If Supabase | — | Supabase project URL |
| `SUPABASE_KEY` | If Supabase | — | Supabase anon/service key |
| `SUPABASE_BUCKET` | If Supabase | — | Storage bucket name |

### MinIO (optional — Sprint 3 stretch)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MINIO_URL` | If MinIO | `http://localhost:9000` | MinIO endpoint |
| `MINIO_ACCESS_KEY` | If MinIO | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | If MinIO | `minioadmin` | MinIO secret key |
| `MINIO_BUCKET` | If MinIO | `uploads` | MinIO bucket name |

### CORS

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | Yes | `["http://localhost:5173", "http://localhost:3000"]` | JSON array of allowed origins |

### Recognition — Detection

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USE_PLATE_DETECTION` | No | `true` | Enable YOLO plate detection |
| `PLATE_DETECTION_MODEL` | No | `yolov8n.pt` | Path to YOLO weights |
| `PLATE_DETECTION_CONFIDENCE` | No | `0.5` | Minimum detection confidence |
| `USE_ONNX_INFERENCE` | No | `false` | Use ONNX Runtime instead of PyTorch (Sprint 4+) |
| `ONNX_MODEL_PATH` | If ONNX | `models/onnx/yolov8-plate-v1.onnx` | Path to ONNX model |

### Recognition — OCR

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OCR_MIN_CONFIDENCE` | No | `0.3` | Minimum OCR character confidence |
| `OCR_GPU` | No | `false` | Enable GPU for EasyOCR |

### Recognition — Confidence Thresholds

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEEDS_REVIEW_THRESHOLD` | No | `0.6` | Below → `NEEDS_REVIEW` status |
| `AUTO_ACCEPT_THRESHOLD` | No | `0.85` | Above → auto `COMPLETED` |

### Recognition — Retry

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLE_ENHANCED_RETRY` | No | `true` | Retry with different preprocessing |
| `MAX_PROCESSING_ATTEMPTS` | No | `3` | Max pipeline attempts per request |

### Recognition — Validation

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEFAULT_PLATE_REGION` | No | `BR` | Plate format region code |

### Logging & Debug (Sprint 2+)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | No | `json` | `json` or `text` |
| `DEBUG` | No | `false` | Enable debug mode |

---

## Frontend (`apps/web/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | `` (empty) | API base URL. Empty = use Vite dev proxy |

**Dev proxy** (in `vite.config.ts`): `/api` → `http://localhost:8000`, `/uploads` → `http://localhost:8000`

**Production (nginx):** Same-origin `/api` and `/uploads` proxied to backend container.

---

## Docker Compose (root `.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_USER` | No | `postgres` | PostgreSQL user |
| `POSTGRES_PASSWORD` | No | `postgres` | PostgreSQL password |
| `POSTGRES_DB` | No | `plate_recognition` | Database name |
| `COMPOSE_PROFILES` | No | — | `dev`, `prod` |

---

## Example Files

### Root `.env.example` (aggregated)

```env
# Copy to .env and adjust

# PostgreSQL (docker-compose)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=plate_recognition

# Backend — see apps/api/.env.example for full list
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/plate_recognition
REDIS_URL=redis://localhost:6379/0
STORAGE_TYPE=local
UPLOAD_DIR=uploads
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
LOG_LEVEL=INFO

# Frontend
VITE_API_URL=
```

### Quick setup

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env   # create in Sprint 0
```

---

## Variable Ownership

| Category | Owner track | Reviewers |
|----------|-------------|-----------|
| DATABASE_*, REDIS_* | DevOps | Backend |
| STORAGE_*, MINIO_* | DevOps + Backend | — |
| CORS_* | Backend | Frontend, DevOps |
| USE_PLATE_*, OCR_*, ONNX_* | AI Engineer | Backend |
| NEEDS_REVIEW_*, AUTO_ACCEPT_* | AI Engineer | Backend |
| VITE_* | Frontend | DevOps |
| LOG_* | DevOps | Backend |
