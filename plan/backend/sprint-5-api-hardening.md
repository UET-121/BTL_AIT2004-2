# Sprint 5 — API Hardening (Tuần 11–12)

**Dates:** 2026-09-01 → 2026-09-14  
**Sprint Goal:** Input validation hardened, rate limiting, ≥ 70% test coverage on core modules.

---

## 1. Input Validation Hardening (Ngày 1–3)

- [ ] **File size limit:** Reject > 10MB before processing — HTTP 413
- [ ] **Image dimensions:** Min 100×50px — HTTP 400 if too small
- [ ] **Magic bytes check:**
  - [ ] JPEG: `\xff\xd8\xff`
  - [ ] PNG: `\x89PNG\r\n\x1a\n`
  - [ ] Reject mismatch between content-type and magic bytes
- [ ] **Empty file:** Reject 0-byte uploads
- [ ] **Corrupt image:** OpenCV imread fails → 400 "Invalid image file"
- [ ] **Unit tests:** Each validation rule has test case

## 2. Rate Limiting (Ngày 3–4)

- [ ] **Add `slowapi` to requirements.txt**
- [ ] **Configure limiter:** 10 uploads/minute/IP on POST `/api/v1/recognition`
- [ ] **Response 429:** `{"detail": "Too many requests"}`
- [ ] **Dev bypass (optional):** Disable when `DEBUG=true`
- [ ] **Test:** 11 rapid uploads → 11th returns 429

## 3. API Versioning (Ngày 4–5)

- [ ] **Response header:** `X-API-Version: v1` on all API responses
- [ ] **Middleware:** Add version header in FastAPI middleware
- [ ] **Document:** Versioning policy in API contracts doc

## 4. Optional Enhancements (Ngày 5–6)

- [ ] **Idempotency key (stretch):** Header `X-Idempotency-Key` on POST
  - [ ] Store key → request_id mapping in Redis with TTL 24h
  - [ ] Duplicate key returns existing request_id
- [ ] **Cursor pagination (stretch):** For lists > 1000 items
  - [ ] Query param `cursor` instead of offset
  - [ ] Only implement if performance testing shows need

## 5. Test Coverage (Ngày 6–9)

- [ ] **pytest-cov configured:** `--cov=app --cov-report=term-missing`
- [ ] **Target ≥ 70%** for:
  - [ ] `app/api/`
  - [ ] `app/services/`
  - [ ] `app/worker/`
- [ ] **Fill gaps identified by coverage report:**
  - [ ] Error paths in routes
  - [ ] Storage edge cases
  - [ ] Task retry logic
  - [ ] Validation branches
- [ ] **CI gate:** `make ci` fails if coverage < 70%

## 6. Extended Health (Coordinate DevOps) (Ngày 7–8)

- [ ] **Implement extended `/health`:**
  - [ ] Ping DB: `SELECT 1`
  - [ ] Ping Redis: connection check
  - [ ] Return component statuses
- [ ] **503 if critical dep down:** Optional strict mode via env

## 7. Security Review (Ngày 9–10)

- [ ] **No path traversal:** Upload filename sanitized (Sprint 3)
- [ ] **No SQL injection:** Parameterized queries only (SQLAlchemy ORM)
- [ ] **CORS not wildcard in prod:** Verify prod profile uses explicit origins
- [ ] **File type sniffing:** Magic bytes prevent polyglot uploads
- [ ] **Document known gaps:** No auth in v1.0 — note in README

---

## Deliverables

| Artifact | Path |
|----------|------|
| Validation logic | `apps/api/app/api/routes.py` |
| Rate limiter | `apps/api/app/main.py` |
| Tests | `apps/api/tests/` (expanded) |
| Coverage config | `pyproject.toml` or `pytest.ini` |

## Verification

- [ ] `pytest --cov=app --cov-fail-under=70` passes
- [ ] Rate limit test passes
- [ ] Invalid files rejected with correct status codes
