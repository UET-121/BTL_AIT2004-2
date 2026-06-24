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
| | | `postgresql+asyncpg://postgres:postgres@localhost:5433/plate_recognition` | Local dev (port 5433 host) |
| | | `postgresql+asyncpg://postgres:postgres@db:5432/plate_recognition` | Docker compose |

### Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STORAGE_TYPE` | Yes | `minio` | `local` hoặc `minio` |
| `UPLOAD_DIR` | Yes | `uploads` | Local upload directory |
| | | `/app/uploads` | Docker container path |

### MinIO (Required when STORAGE_TYPE=minio)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MINIO_URL` | Yes | `http://localhost:9000` (host) hoặc `http://minio:9000` (Docker) | MinIO endpoint |
| `MINIO_PUBLIC_URL` | Yes | `http://localhost:9000` | Public URL for media access |
| `MINIO_ACCESS_KEY` | Yes | `minioadmin` | MinIO root/access key |
| `MINIO_SECRET_KEY` | Yes | `minioadmin` | MinIO root/secret key |
| `MINIO_BUCKET` | Yes | `uploads` | MinIO bucket name |

### CORS

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | Yes | `["http://localhost:5173", "http://127.0.0.1:5173"]` | JSON array of allowed origins |

### Recognition — Detection

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLATE_DETECTION_MODEL` | No | `license_plate_detector.pt` | Path to YOLO weights |
| `USE_ONNX_INFERENCE` | No | `true` | Use ONNX Runtime for inference |
| `ONNX_MODEL_PATH` | If ONNX | `models/onnx/yolov8-plate-v1.onnx` | Path to ONNX model |

### Recognition — OCR

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OCR_GPU` | No | `false` | Enable GPU for EasyOCR |

### Recognition — Validation

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEFAULT_PLATE_REGION` | No | `GB` | Plate format region code (e.g. `GB` or `BR`) |

### Logging & Debug

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
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

# Backend — apps/api
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/plate_recognition
STORAGE_TYPE=minio
UPLOAD_DIR=uploads
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
LOG_LEVEL=INFO

# MinIO
MINIO_PUBLIC_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=uploads
OCR_GPU=false

# Frontend
VITE_API_URL=
```

### Quick setup

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp frontend/.env.example frontend/.env
```

---

## Variable Ownership

| Category | Owner track | Reviewers |
|----------|-------------|-----------|
| DATABASE_* | DevOps | Backend |
| STORAGE_*, MINIO_* | DevOps + Backend | — |
| CORS_* | Backend | Frontend, DevOps |
| PLATE_DETECTION_*, OCR_*, ONNX_* | AI Engineer | Backend |
| VITE_* | Frontend | DevOps |
| LOG_* | DevOps | Backend |
