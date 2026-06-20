# Sprint 0 — Foundation (Tuần 1–2)

**Dates:** 2026-06-23 → 2026-07-06  
**Sprint Goal:** Mọi dev clone repo và chạy được DB + Redis; env template và self docs sẵn sàng.

---

## 1. Chuẩn bị môi trường & Khởi tạo dự án (Ngày 1–2)

- [ ] **Chuẩn hóa monorepo layout:** Xác nhận cấu trúc `apps/api`, `apps/web`, `plan/`, `data/` (gitignored), `models/` (DVC), `scripts/`, `datasets/`, `notebooks/`
- [ ] **Tạo thư mục `data/`:** `data/pg/`, `data/redis/`, `data/backups/` — thêm vào `.gitignore`
- [ ] **Tạo thư mục `models/`:** `models/detection/`, `models/onnx/`, `models/release/` với `.gitkeep`
- [ ] **Review `.gitignore` master:** Bổ sung `data/`, `uploads/`, `*.pt`, `.env`, `__pycache__/`, `node_modules/`, `.ipynb_checkpoints/`
- [ ] **Verify Python version:** Document yêu cầu Python 3.12+ trong DevOps README
- [ ] **Verify Node/pnpm:** Document yêu cầu Node 20+, pnpm 9+ cho frontend

## 2. Docker Compose — Infrastructure Only (Ngày 2–3)

- [ ] **Khởi tạo `docker-compose.yml` v2:** Giữ services `db` (PostgreSQL 16-alpine) + `redis` (7-alpine)
- [ ] **Volume paths:** Sửa volume mount → `./data/pg:/var/lib/postgresql/data`, `./data/redis:/data`
- [ ] **Healthcheck `db`:** `pg_isready -U postgres`, interval 5s, retries 5
- [ ] **Healthcheck `redis`:** `redis-cli ping`, interval 5s, retries 5
- [ ] **Port mapping:** `5432:5432` (db), `6379:6379` (redis) — document conflict nếu port đã dùng
- [ ] **Verify startup:** `docker compose up -d` → cả 2 services healthy trong 30s
- [ ] **Verify connectivity:** `psql` hoặc `docker compose exec db psql -U postgres -c '\l'` thành công

## 3. Environment & Configuration (Ngày 3–4)

- [ ] **Tạo root `.env.example`:** Aggregated env cho docker-compose (POSTGRES_*, DATABASE_URL, REDIS_URL)
- [ ] **Sync `plan/_shared/06-env-variables.md`:** Liệt kê toàn bộ biến backend + `VITE_API_URL`
- [ ] **Document copy workflow:** `cp .env.example .env` + `cp apps/api/.env.example apps/api/.env`
- [ ] **Validate CORS origins:** `CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]` match frontend dev port
- [ ] **Tạo `apps/web/.env.example`:** `VITE_API_URL=` (empty = proxy mode)

## 4. Makefile & Scripts (Ngày 4–5)

- [ ] **Tạo root `Makefile`:** Targets `help`, `docker-up`, `docker-down`, `docker-logs`, `models`
- [ ] **Wrapper targets:** `make api` → `cd apps/api && make api`; `make worker` → tương tự
- [ ] **Target `make docker-up`:** `docker compose up -d db redis`
- [ ] **Target `make docker-down`:** `docker compose down`
- [ ] **Target `make docker-logs`:** `docker compose logs -f`
- [ ] **Tạo `scripts/wait-for-it.sh`:** Chờ TCP port ready (db:5432, redis:6379) với timeout 60s
- [ ] **Script executable:** `chmod +x scripts/wait-for-it.sh` (document cho Windows: Git Bash/WSL)

## 5. DVC & Model Artifacts (Ngày 5–6)

- [ ] **Document DVC setup:** Cài `dvc[gdrive]`, configure remote từ [`.dvc/config`](../../.dvc/config)
- [ ] **Document model pull:** `cd apps/api && dvc pull` → tải `yolov8n.pt`
- [ ] **Fallback manual download:** Ghi hướng dẫn nếu DVC Google Drive fail (R07 risk)
- [ ] **Makefile target `make models`:** Chạy `dvc pull` trong `apps/api`
- [ ] **Verify model exists:** Sau pull, file `apps/api/yolov8n.pt` hoặc path trong `PLATE_DETECTION_MODEL`

## 6. Docker Compose Override Template (Ngày 6–7)

- [ ] **Tạo `docker-compose.override.yml.example`:** Template mount source code cho dev
- [ ] **Example volume mounts:** `./apps/api/app:/app/app` cho hot reload (commented, dùng Sprint 1)
- [ ] **Document usage:** `cp docker-compose.override.yml.example docker-compose.override.yml`
- [ ] **Gitignore override file:** `docker-compose.override.yml` không commit (local dev only)

## 7. Documentation & Dev Workflow (Ngày 7–8)

- [ ] **Viết dev workflow trong `plan/devops/README.md`:** Step-by-step từ clone → chạy
- [ ] **Document prerequisites:** Docker Desktop, Python 3.12, Node 20, pnpm, (optional) DVC
- [ ] **Document port map:** 5432 PG, 6379 Redis, 8000 API, 5173 Vite, 80 nginx
- [ ] **Troubleshooting section:** Port conflict, Docker not running, permission denied on `data/`
- [ ] **Link cross-team deps:** Backend cần `alembic.ini`; Frontend cần Vite proxy

## 8. Verification Checklist (Ngày 9–10)

- [ ] **Fresh clone test:** Clone repo mới → `make docker-up` → db + redis healthy
- [ ] **Env test:** Copy `.env.example` → services connect được từ host
- [ ] **Script test:** `./scripts/wait-for-it.sh localhost 5432` exit 0 khi db up
- [ ] **Docs review:** DevOps README đủ để dev mới không cần hỏi thêm về infra
- [ ] **Integration unblock:** Backend Sprint 0 có thể chạy `make migrate` (phụ thuộc alembic.ini)
- [ ] **Sprint Review demo:** `docker compose ps` shows 2 healthy services

---

## Deliverables

| Artifact | Path |
|----------|------|
| Docker compose (infra) | `docker-compose.yml` |
| Root Makefile | `Makefile` |
| Env template | `.env.example`, `apps/web/.env.example` |
| Wait script | `scripts/wait-for-it.sh` |
| DevOps README | `plan/devops/README.md` |
| Env reference | `plan/_shared/06-env-variables.md` |

## Dependencies

| Waiting on | From track | Needed by |
|------------|------------|-----------|
| `alembic.ini` | Backend | `make migrate` verification |
| `/health` endpoint | Backend | Sprint 1 healthcheck |

## Stretch Goals

- [ ] ** direnv support:** `.envrc` auto-load env khi cd vào repo
- [ ] **Devcontainer config:** `.devcontainer/devcontainer.json` cho VS Code
