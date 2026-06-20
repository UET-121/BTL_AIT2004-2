# Sprint 2 — Async Worker (Tuần 5–6)

**Dates:** 2026-07-21 → 2026-08-03  
**Sprint Goal:** Celery worker xử lý recognition async, status lifecycle hoàn chỉnh.

---

## 1. Celery Application (Ngày 1–2)

- [ ] **[`celery_app.py`](../../apps/api/app/worker/celery_app.py):**
  - [ ] App name: `plate_recognition`
  - [ ] Broker: `REDIS_URL` from settings
  - [ ] Result backend: optional (Redis or disable)
  - [ ] Serialization: JSON
  - [ ] Timezone: UTC
  - [ ] `task_track_started=True`
- [ ] **Auto-discover tasks:** `app.autodiscover_tasks(['app.worker'])`
- [ ] **Verify connection:** Worker starts, connects to Redis

## 2. Recognition Task (Ngày 2–4)

- [ ] **[`tasks.py`](../../apps/api/app/worker/tasks.py) — `process_plate_recognition`:**
  - [ ] Input: `request_id: str`
  - [ ] Load request from DB
  - [ ] Update status → `PENDING`
  - [ ] Call RecognitionService (stub OK this sprint, full Sprint 4)
  - [ ] Update result fields: plate_number, confidence, status
  - [ ] Handle exceptions → status `FAILED`, error_message
  - [ ] `soft_time_limit=300`, `time_limit=360`
  - [ ] `max_retries=3`, `default_retry_delay=60`
- [ ] **Idempotent recheck:** Skip if already COMPLETED (unless reprocess)

## 3. Queue on Upload (Ngày 4–5)

- [ ] **Update POST endpoint:** After DB insert, call `process_plate_recognition.delay(str(request_id))`
- [ ] **Response unchanged:** Return immediately with NOT_STARTED status
- [ ] **Verify async:** API returns before processing completes
- [ ] **Verify worker picks up:** Status changes NOT_STARTED → PENDING → terminal

## 4. Status Lifecycle (Ngày 5–6)

- [ ] **Document state machine:**
  ```
  NOT_STARTED → PENDING → COMPLETED
                       → NEEDS_REVIEW
                       → FAILED
  ```
- [ ] **Reprocess path:** FAILED/NEEDS_REVIEW → NOT_STARTED → PENDING → ...
- [ ] **Timestamps:** Update `updated_at` on each status change
- [ ] **Log transitions:** INFO level with request_id

## 5. Worker DB Session (Ngày 6–7)

- [ ] **Sync session in worker:** Celery tasks are sync — use sync SQLAlchemy session or `asyncio.run()`
- [ ] **Recommended:** Create sync engine from DATABASE_URL (replace asyncpg with psycopg2 for worker)
- [ ] **Alternative:** `asyncio.run(process_async(request_id))` wrapper
- [ ] **Session lifecycle:** Open → commit → close per task
- [ ] **Error rollback:** Rollback on exception

## 6. Migrations 002–003 (Ngày 7–8)

- [ ] **Migration 002:** [`002_add_confidence_and_detection_fields.py`](../../apps/api/migrations/versions/002_add_confidence_and_detection_fields.py)
  - [ ] Add: confidence_score, detection_confidence, ocr_confidence
  - [ ] Add: needs_review, bounding_box (JSON), plate_region
- [ ] **Migration 003:** [`003_add_not_started_status.py`](../../apps/api/migrations/versions/003_add_not_started_status.py)
  - [ ] Add NOT_STARTED to status enum
- [ ] **Run on fresh DB:** All 3 migrations sequential
- [ ] **Update schemas:** Response includes new fields

## 7. Integration Test (Ngày 8–10)

- [ ] **Manual test flow:**
  1. [ ] Start redis, db, api, worker
  2. [ ] POST upload image
  3. [ ] Poll GET until terminal status
  4. [ ] Verify plate_number populated (or FAILED with message)
- [ ] **Test reprocess:** FAILED request → reprocess → new attempt
- [ ] **Test worker crash recovery:** Kill worker mid-task → restart → task retried or marked FAILED
- [ ] **Coordinate DevOps Sprint 2:** Request ID propagation in logs

---

## Deliverables

| Artifact | Path |
|----------|------|
| Celery app | `apps/api/app/worker/celery_app.py` |
| Task | `apps/api/app/worker/tasks.py` |
| Migrations 002–003 | `apps/api/migrations/versions/` |
| Updated routes | Queue on upload |

## Dependencies

| From | Need |
|------|------|
| Sprint 1 | API + DB model |
| DevOps Sprint 0 | Redis running |
| AI Sprint 2+ | RecognitionService (stub returns mock OK for now)
