# Sprint 3 — Storage & DB (Tuần 7–8)

**Dates:** 2026-08-04 → 2026-08-17  
**Sprint Goal:** Storage abstraction hoàn chỉnh, reprocess endpoint, DB connection pool tuned.

---

## 1. StorageService Abstract (Ngày 1–2)

- [ ] **[`storage.py`](../../apps/api/app/services/storage.py) — interface:**
  - [ ] `async def save(filename: str, content: bytes) -> str` — returns URL/path
  - [ ] `async def get_url(filename: str) -> str`
  - [ ] `async def delete(filename: str) -> None`
- [ ] **Factory:** `get_storage_service()` reads `STORAGE_TYPE` env
- [ ] **FastAPI dependency:** Inject via `Depends(get_storage_service)`

## 2. LocalStorage Implementation (Ngày 2–3)

- [ ] **LocalStorage class:**
  - [ ] Save to `{UPLOAD_DIR}/{filename}`
  - [ ] Return URL: `/uploads/{filename}`
  - [ ] Auto-create upload directory
  - [ ] Delete removes file from disk
- [ ] **Default storage type:** `STORAGE_TYPE=local`
- [ ] **Verify static mount:** Saved files accessible via `GET /uploads/{filename}`

## 3. Filename Sanitization (Ngày 3)

- [ ] **UUID-based names:** `{uuid4}.{ext}` — never use raw user filename for storage
- [ ] **Extension whitelist:** jpg, jpeg, png only
- [ ] **Magic bytes validation (prep Sprint 5):** Check file header matches extension
- [ ] **Original filename:** Optionally store in metadata (future), not used as path

## 4. MinIO Local (Stretch) (Ngày 4–5)

- [ ] **Add `minio` to requirements.txt**
- [ ] **MinioStorage class:** Implement save/get_url/delete
- [ ] **Env vars:** MINIO_URL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET
- [ ] **Docker compose service (coordinate DevOps):** MinIO on port 9000
- [ ] **Test:** `STORAGE_TYPE=minio` → upload → retrieve via presigned URL
- [ ] **If deferred:** Document S3/Supabase stubs remain NotImplemented

## 5. DB Connection Pool (Ngày 5–6)

- [ ] **Engine config in [`database.py`](../../apps/api/app/shared/database.py):**
  - [ ] `pool_size=5`
  - [ ] `max_overflow=10`
  - [ ] `pool_pre_ping=True` — reconnect on stale connections
  - [ ] `pool_recycle=3600`
- [ ] **Session config:** `expire_on_commit=False` for async patterns
- [ ] **Load test (informal):** 20 concurrent GET requests — no pool exhaustion errors

## 6. Reprocess Endpoint (Ngày 6–8)

- [ ] **`POST /api/v1/recognition/{id}/reprocess`** (port from existing [`routes.py`](../../apps/api/app/api/routes.py)):
  - [ ] Allow status: FAILED, NEEDS_REVIEW only
  - [ ] Reset: plate_number, error_message, confidence fields, bbox, needs_review
  - [ ] Set status → NOT_STARTED
  - [ ] Enqueue Celery task
  - [ ] Return RecognitionRequestSubmitResponse
  - [ ] 400 if status is COMPLETED or PENDING
  - [ ] 404 if not found
- [ ] **Test:** Reprocess NEEDS_REVIEW → new processing → updated result

## 7. Tests (Ngày 8–10)

- [ ] **Storage unit tests:** Save, get_url, delete cycle
- [ ] **Reprocess API test:** FAILED → reprocess → 200 + NOT_STARTED
- [ ] **Reprocess invalid status:** COMPLETED → 400
- [ ] **Upload + retrieve:** File saved and served via /uploads

---

## Deliverables

| Artifact | Path |
|----------|------|
| Storage service | `apps/api/app/services/storage.py` |
| Reprocess endpoint | `apps/api/app/api/routes.py` |
| Pool config | `apps/api/app/shared/database.py` |
| Tests | `apps/api/tests/services/test_storage.py` |

## Dependencies

| From | Need |
|------|------|
| Sprint 2 | Celery queue for reprocess |
| DevOps (stretch) | MinIO docker service |
