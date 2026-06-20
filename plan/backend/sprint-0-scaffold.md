# Sprint 0 — Scaffold (Tuần 1–2)

**Dates:** 2026-06-23 → 2026-07-06  
**Sprint Goal:** FastAPI app chạy với `/health`, CORS, config, alembic, và project layout chuẩn.

---

## 1. Chuẩn bị môi trường & Khởi tạo dự án (Ngày 1)

- [ ] **Khởi tạo FastAPI:** Tạo/verify `apps/api/app/main.py`, app FastAPI cơ bản chạy với `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- [ ] **Cấu hình CORS:** Thêm `CORSMiddleware`, `allow_origins` đọc từ env `CORS_ORIGINS=["http://localhost:5173"]` (match [`config.py`](../../apps/api/app/shared/config.py))
- [ ] **Allow methods:** `GET, POST, PUT, DELETE, OPTIONS`
- [ ] **Allow headers:** `*` hoặc explicit `Content-Type, X-Request-ID`
- [ ] **Allow credentials:** `true` nếu frontend cần cookies (future)

## 2. Quản lý Dependencies (Ngày 1–2)

- [ ] **Tạo/verify `requirements.txt`:**
  - [ ] `fastapi>=0.115.0`
  - [ ] `uvicorn[standard]>=0.32.0`
  - [ ] `python-multipart` — file upload
  - [ ] `sqlalchemy[asyncio]>=2.0`
  - [ ] `asyncpg` — async PostgreSQL driver
  - [ ] `alembic` — migrations
  - [ ] `celery>=5.4`
  - [ ] `redis` — Celery broker client
  - [ ] `pydantic-settings` — env config
  - [ ] `python-dotenv` — .env loading
  - [ ] `easyocr`, `opencv-python-headless`, `ultralytics`, `numpy` — ML deps
- [ ] **Pin major versions:** Document pinning policy
- [ ] **Install verify:** `pip install -r requirements.txt` in clean venv

## 3. Environment Configuration (Ngày 2)

- [ ] **Tạo/verify `.env.example`:** Tất cả biến từ [`apps/api/.env.example`](../../apps/api/.env.example)
- [ ] **Bổ sung biến mới:**
  - [ ] `LOG_LEVEL=INFO`
  - [ ] `USE_ONNX_INFERENCE=false`
  - [ ] `ONNX_MODEL_PATH=models/onnx/yolov8-plate-v1.onnx`
- [ ] **Pydantic Settings:** [`shared/config.py`](../../apps/api/app/shared/config.py) — load và validate tất cả biến
- [ ] **Settings singleton:** `get_settings()` cached with `@lru_cache`
- [ ] **Sync với [`06-env-variables.md`](../_shared/06-env-variables.md)**

## 4. Application Structure (Ngày 2–3)

- [ ] **Project layout verify:**
  ```
  apps/api/app/
  ├── main.py
  ├── api/routes.py
  ├── models/recognition.py, schemas.py
  ├── services/
  ├── worker/celery_app.py, tasks.py
  └── shared/config.py, database.py
  ```
- [ ] **Package `__init__.py`:** All directories importable
- [ ] **Router mount:** `app.include_router(router)` in main.py
- [ ] **API prefix:** `/api/v1/recognition`

## 5. Health & Static Files (Ngày 3–4)

- [ ] **Health endpoint:** `GET /health` → `{"status": "ok"}`
- [ ] **Static files:** Mount `/uploads` → `UPLOAD_DIR` for local storage
- [ ] **Create uploads dir:** Auto-create on startup if not exists
- [ ] **OpenAPI metadata:** Title, description, version in FastAPI constructor

## 6. Database Setup (Ngày 4–5)

- [ ] **Async engine:** [`database.py`](../../apps/api/app/shared/database.py) — `create_async_engine(DATABASE_URL)`
- [ ] **Session factory:** `async_sessionmaker` with `get_db()` dependency
- [ ] **Base model:** SQLAlchemy `DeclarativeBase`
- [ ] **Connection test:** Startup event ping DB (optional Sprint 2)

## 7. Alembic Configuration (Ngày 5–6) — CRITICAL

- [ ] **Tạo `apps/api/alembic.ini`:** Fix gap hiện tại
  ```ini
  [alembic]
  script_location = migrations
  sqlalchemy.url = driver://user:pass@localhost/dbname
  ```
- [ ] **Override URL in [`migrations/env.py`](../../apps/api/migrations/env.py):** Read `DATABASE_URL` from settings (sync URL for alembic)
- [ ] **Verify `make migrate`:** Runs `alembic upgrade head` successfully
- [ ] **Verify `make migrate-create MSG='test'`:** Generates new migration file

## 8. Makefile & Dev Commands (Ngày 6–7)

- [ ] **Verify [`Makefile`](../../apps/api/Makefile) targets:**
  - [ ] `install` — pip install
  - [ ] `api` — uvicorn with reload
  - [ ] `worker` — celery worker
  - [ ] `migrate` — alembic upgrade head
  - [ ] `migrate-create MSG='...'` — autogenerate
  - [ ] `migrate-down` — downgrade -1
- [ ] **Test workflow:** docker-up db → migrate → api → curl health

## 9. Verification (Ngày 8–10)

- [ ] **`curl http://localhost:8000/health`** → 200
- [ ] **`curl http://localhost:8000/docs`** → Swagger UI loads
- [ ] **CORS test:** Frontend origin không bị block (OPTIONS preflight)
- [ ] **Upload dir writable:** App creates file in uploads/
- [ ] **Unblock DevOps:** health endpoint ready for Sprint 1 docker healthcheck

---

## Deliverables

| Artifact | Path |
|----------|------|
| FastAPI app | `apps/api/app/main.py` |
| Config | `apps/api/app/shared/config.py` |
| Alembic | `apps/api/alembic.ini` |
| Env template | `apps/api/.env.example` |

## Blockers

- DevOps Sprint 0: PostgreSQL running for migrate test
- Missing `alembic.ini` is R05 critical risk — must fix this sprint
