# Sprint 1 — Local Stack (Tuần 3–4)

**Dates:** 2026-07-07 → 2026-07-20  
**Sprint Goal:** `docker compose up -d` khởi động đủ 5 services (db, redis, app, worker, web) healthy.

---

## 1. Enable Backend Service `app` (Ngày 1–2)

- [ ] **Uncomment service `app` trong `docker-compose.yml`:** Build context `apps/api`, dockerfile `Dockerfile`
- [ ] **Environment variables:** `DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/plate_recognition`
- [ ] **Redis URL:** `REDIS_URL=redis://redis:6379/0`
- [ ] **Storage:** `STORAGE_TYPE=local`, `UPLOAD_DIR=/app/uploads`
- [ ] **CORS:** `CORS_ORIGINS='["http://localhost:5173", "http://localhost:80", "http://localhost"]'`
- [ ] **Port mapping:** `8000:8000`
- [ ] **depends_on:** `db` và `redis` với `condition: service_healthy`
- [ ] **Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000` (production) hoặc dùng Dockerfile CMD

## 2. Enable Celery Worker Service (Ngày 2–3)

- [ ] **Uncomment service `worker`:** Shared build context/image với `app`
- [ ] **Command override:** `celery -A app.worker.celery_app worker --loglevel=info`
- [ ] **Shared env:** Same DATABASE_URL, REDIS_URL, UPLOAD_DIR, model env vars
- [ ] **depends_on:** `db`, `redis`, `app` (condition: service_healthy)
- [ ] **No port expose:** Worker không cần port mapping
- [ ] **Concurrency:** Document `--concurrency=1` cho local (EasyOCR memory)

## 3. Enable Frontend Service `web` (Ngày 3–4)

- [ ] **Uncomment service `web`:** Build context `apps/web`, dockerfile `Dockerfile`
- [ ] **Port mapping:** `80:80`
- [ ] **depends_on:** `app` (condition: service_healthy)
- [ ] **Verify nginx proxy:** `/api` → `http://app:8000`, `/uploads` → `http://app:8000/uploads`
- [ ] **SPA routing:** `try_files $uri /index.html` cho client-side routes
- [ ] **Static assets caching:** Cache headers cho `/assets/*`

## 4. Shared Volumes & Networks (Ngày 4–5)

- [ ] **Named volume `uploads_data`:** Mount `/app/uploads` cho cả `app` và `worker`
- [ ] **Verify upload persistence:** Upload file → restart worker → file vẫn accessible
- [ ] **Network `plate-net`:** Tạo custom bridge network, attach tất cả services
- [ ] **Internal DNS:** Services resolve `db`, `redis`, `app` by name
- [ ] **Production profile:** Document không expose 5432/6379 ngoài host khi `--profile prod`

## 5. Fix API Dockerfile (Ngày 5–6)

- [ ] **Base image:** `python:3.12-slim`
- [ ] **System deps:** `apt-get install -y libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev`
- [ ] **Multi-stage (optional):** Builder stage cài deps, runtime stage copy venv
- [ ] **Copy requirements.txt:** `pip install -r requirements.txt` trước copy app code (cache layer)
- [ ] **Copy app code:** `COPY app/ /app/app/`, `COPY migrations/ /app/migrations/`
- [ ] **Model weights:** COPY `yolov8n.pt` hoặc RUN step `dvc pull` (document trade-off image size)
- [ ] **WORKDIR /app:** CMD uvicorn
- [ ] **Non-root user (stretch):** Run as `appuser` uid 1000

## 6. Fix Web Dockerfile (Ngày 6–7)

- [ ] **Stage 1 — build:** `node:20-alpine`, `pnpm install`, `pnpm build`
- [ ] **Stage 2 — serve:** `nginx:alpine`, copy `dist/` → `/usr/share/nginx/html`
- [ ] **Copy nginx.conf:** Proxy rules từ [`apps/web/nginx.conf`](../../apps/web/nginx.conf)
- [ ] **Build arg `VITE_API_URL`:** Empty cho same-origin proxy
- [ ] **Verify build:** `docker compose build web` thành công < 5 phút

## 7. Healthchecks (Ngày 7–8)

- [ ] **Healthcheck `app`:** `curl -f http://localhost:8000/health` hoặc Python urllib
- [ ] **Interval:** 10s, timeout 5s, retries 5, start_period 30s (EasyOCR first load)
- [ ] **Worker health (optional):** `celery inspect ping` — document complexity, defer nếu cần
- [ ] **Web health:** `curl -f http://localhost:80/` returns 200
- [ ] **Compose depends_on conditions:** Tất cả chains verified

## 8. Dev Compose Overlay (Ngày 8–9)

- [ ] **Tạo `docker-compose.dev.yml`:** Override cho development
- [ ] **App command dev:** `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- [ ] **Volume mount source:** `./apps/api/app:/app/app` cho hot reload
- [ ] **Web dev alternative:** Document chạy `pnpm dev` ngoài docker thay vì nginx
- [ ] **Usage:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`

## 9. One-Command Startup Verification (Ngày 9–10)

- [ ] **Full startup test:** `docker compose up -d --build` → 5 services running
- [ ] **Health timing:** Tất cả healthy trong < 3 phút (document actual time)
- [ ] **API test:** `curl http://localhost:8000/health` → `{"status":"ok"}`
- [ ] **Web test:** Browser `http://localhost` loads React app
- [ ] **Upload test:** POST image qua nginx proxy `http://localhost/api/v1/recognition`
- [ ] **Worker test:** Task processed, status changes in DB
- [ ] **Teardown test:** `docker compose down` clean, `docker compose up -d` reproducible
- [ ] **Document in README:** One-command startup instructions

---

## Deliverables

| Artifact | Path |
|----------|------|
| Full docker-compose | `docker-compose.yml` |
| Dev overlay | `docker-compose.dev.yml` |
| API Dockerfile | `apps/api/Dockerfile` |
| Web Dockerfile | `apps/web/Dockerfile` |

## Blockers to Watch

- Backend `/health` must exist (Sprint 0 Backend)
- API Dockerfile build may fail on OpenCV deps — test early Day 5
- Model file size inflates image — consider volume mount for `models/`

## Stretch Goals

- [ ] **MinIO service:** Add optional MinIO container for object storage testing
- [ ] **docker compose watch:** Enable `develop.watch` for auto-sync (Compose v2.22+)
