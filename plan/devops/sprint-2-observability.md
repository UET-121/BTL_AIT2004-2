# Sprint 2 — Observability (Tuần 5–6)

**Dates:** 2026-07-21 → 2026-08-03  
**Sprint Goal:** Structured logging, extended health checks, và smoke test script tự động hóa verification.

---

## 1. Structured Logging (Ngày 1–3)

- [ ] **Add dependency:** `python-json-logger` vào `apps/api/requirements.txt`
- [ ] **Logging config module:** `apps/api/app/shared/logging.py` — configure root logger
- [ ] **JSON format:** Output `{"timestamp", "level", "message", "request_id", "service"}` 
- [ ] **Env `LOG_LEVEL`:** Default `INFO`, support `DEBUG` for dev
- [ ] **Env `LOG_FORMAT`:** `json` (docker) or `text` (local dev readability)
- [ ] **Apply to FastAPI:** Configure in `main.py` startup event
- [ ] **Apply to Celery worker:** Configure in `celery_app.py` worker_process_init signal
- [ ] **Suppress noisy loggers:** urllib3, sqlalchemy.engine → WARNING

## 2. Request ID Middleware (Ngày 3–4)

- [ ] **FastAPI middleware:** Generate UUID `X-Request-ID` nếu client không gửi
- [ ] **Echo header:** Return `X-Request-ID` in response headers
- [ ] **Log correlation:** Mọi log trong request context gắn `request_id`
- [ ] **Celery propagation:** Pass `request_id` as task kwarg từ API → worker
- [ ] **Worker logs:** Include `request_id` + `recognition_request_id` in task logs
- [ ] **Test:** Upload → grep logs for same request_id across API and worker

## 3. Extended Health Endpoint (Ngày 4–5)

- [ ] **Coordinate with Backend:** Extend `GET /health` response schema
- [ ] **DB ping:** Execute `SELECT 1` via async session, report `db: connected|error`
- [ ] **Redis ping:** Celery broker connection check, report `redis: connected|error`
- [ ] **Aggregate status:** Return `503` if any critical dep down (optional, document behavior)
- [ ] **Version field:** `version: "1.0.0"` from env or package metadata
- [ ] **Docker healthcheck update:** Parse JSON response, verify `status == ok`
- [ ] **Document health response:** Update [`05-api-contracts.md`](../_shared/05-api-contracts.md)

## 4. Celery Flower — Dev Only (Ngày 5–6)

- [ ] **Add flower service:** Profile `dev` only in docker-compose
- [ ] **Image/command:** `celery -A app.worker.celery_app flower --port=5555`
- [ ] **Port mapping:** `5555:5555`
- [ ] **depends_on:** redis, worker
- [ ] **Document access:** `http://localhost:5555` — task monitor, queue depth
- [ ] **Security note:** Never expose in prod profile

## 5. Log Rotation (Ngày 6–7)

- [ ] **Docker logging driver:** Set `logging: driver: json-file`, `options: max-size: 10m, max-file: 3`
- [ ] **Apply to all services:** db, redis, app, worker, web
- [ ] **Document disk usage:** Estimated log size per day local dev
- [ ] **Log inspection commands:** `docker compose logs -f app --tail=100`

## 6. Smoke Test Script (Ngày 7–9)

- [ ] **Tạo `scripts/smoke-test.sh`:** End-to-end verification script
- [ ] **Step 1 — Health:** `curl -sf http://localhost:8000/health` → exit 1 if fail
- [ ] **Step 2 — Upload:** POST sample image to `/api/v1/recognition` (use `images/placa1.jpg` or bundled fixture)
- [ ] **Step 3 — Parse request_id:** Extract UUID from JSON response (jq or python)
- [ ] **Step 4 — Poll status:** Loop GET `/api/v1/recognition/{id}` max 60s, interval 2s
- [ ] **Step 5 — Assert terminal state:** Status in (COMPLETED, NEEDS_REVIEW, FAILED)
- [ ] **Step 6 — Report:** Print summary plate_number, confidence, latency
- [ ] **Exit codes:** 0 success, 1 health fail, 2 upload fail, 3 timeout
- [ ] **Makefile target:** `make smoke-test` runs script
- [ ] **CI integration prep:** Script usable headless in Sprint 4 CI

## 7. Monitoring Documentation (Ngày 9–10)

- [ ] **Runbook section in DevOps README:** How to diagnose common issues via logs
- [ ] **Log query examples:** Find failed tasks, slow requests (>10s)
- [ ] **Dashboard placeholder:** Document future Prometheus/Grafana if cloud deploy
- [ ] **Alerting placeholder:** Document what would trigger alerts in production

---

## Deliverables

| Artifact | Path |
|----------|------|
| Logging config | `apps/api/app/shared/logging.py` |
| Smoke test | `scripts/smoke-test.sh` |
| Flower service | `docker-compose.yml` (profile dev) |

## Dependencies

| From | Need |
|------|------|
| Backend | Extended `/health` implementation |
| Backend | Request ID middleware in FastAPI |
| DevOps Sprint 1 | Full stack running for smoke test |

## Verification

- [ ] `make smoke-test` passes against docker full stack
- [ ] Logs are valid JSON parseable by `jq`
- [ ] Request ID traceable API → worker for single upload
