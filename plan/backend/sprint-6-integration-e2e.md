# Sprint 6 — Integration E2E (Tuần 13–14)

**Dates:** 2026-09-15 → 2026-09-28  
**Sprint Goal:** E2E test in CI, load test report, API docs updated, migration rollback verified.

---

## 1. E2E Test Script (Ngày 1–3)

- [ ] **Tạo `apps/api/tests/e2e/test_full_flow.py`:**
  - [ ] Requires running stack (or testcontainers full stack)
  - [ ] Step 1: POST upload sample plate image
  - [ ] Step 2: Poll GET until terminal status (timeout 60s)
  - [ ] Step 3: Assert status in (COMPLETED, NEEDS_REVIEW)
  - [ ] Step 4: Assert plate_number is not null
  - [ ] Step 5: Assert confidence_score > 0
- [ ] **CLI runner:** `scripts/e2e-test.sh` wraps pytest e2e
- [ ] **CI integration:** Part of `scripts/ci.sh` (requires docker stack)
- [ ] **Mark `@pytest.mark.e2e`:** Separable from unit tests

## 2. Load Test Spike (Ngày 3–5)

- [ ] **Setup locust:** `apps/api/tests/load/locustfile.py`
  - [ ] Scenario: Upload image (10 concurrent users)
  - [ ] Scenario: Poll GET status
  - [ ] Run duration: 2 minutes
- [ ] **Run against local docker stack**
- [ ] **Document results in `plan/backend/LOAD-TEST-REPORT.md`:**
  - [ ] Requests/sec
  - [ ] Failure rate
  - [ ] p50/p95 latency
  - [ ] Worker queue depth over time
  - [ ] Bottleneck analysis
- [ ] **Coordinate DevOps:** Feed into PERFORMANCE-BASELINE.md

## 3. API Documentation Update (Ngày 5–7)

- [ ] **Update root [`README.md`](../../README.md):**
  - [ ] Correct paths: `apps/api`, `apps/web`
  - [ ] All 5 status values documented
  - [ ] All endpoints including reprocess
  - [ ] Confidence fields documented
  - [ ] Docker services table (5 services)
  - [ ] Updated env var reference
- [ ] **Export OpenAPI JSON:** `curl http://localhost:8000/openapi.json > docs/openapi.json`
- [ ] **Verify `/docs` examples match actual behavior**

## 4. Migration Rollback Test (Ngày 7–8)

- [ ] **Fresh DB test:**
  1. [ ] `alembic upgrade head` — all migrations apply
  2. [ ] Insert test data
  3. [ ] `alembic downgrade -1` — revert last migration
  4. [ ] Verify schema change reverted
  5. [ ] `alembic upgrade head` — re-apply successfully
- [ ] **Document migration order:** 001 → 002 → 003 in README
- [ ] **Production note:** Always backup before migrate (link DevOps DR doc)

## 5. Backend Sign-off Checklist (Ngày 8–10)

- [ ] All Sprint 0–6 backend checklists reviewed
- [ ] `make ci` green
- [ ] E2E test pass against prod profile docker stack
- [ ] Coverage ≥ 70%
- [ ] OpenAPI export committed
- [ ] No critical bugs open
- [ ] Handoff to DevOps for release checklist

---

## Deliverables

| Artifact | Path |
|----------|------|
| E2E tests | `apps/api/tests/e2e/` |
| Load test | `apps/api/tests/load/locustfile.py` |
| Load report | `plan/backend/LOAD-TEST-REPORT.md` |
| OpenAPI export | `docs/openapi.json` |
| Updated README | `README.md` |

## Sign-off

| Criteria | Pass |
|----------|------|
| E2E test green | [ ] |
| Load test documented | [ ] |
| README accurate | [ ] |
| Migration rollback verified | [ ] |
| Coverage ≥ 70% | [ ] |
