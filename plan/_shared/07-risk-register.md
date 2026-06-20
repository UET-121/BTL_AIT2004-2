# Risk Register — Cross-Team

Cập nhật sau mỗi Sprint Retrospective. Owner chịu trách nhiệm mitigation.

**Legend:** Probability (L/M/H) | Impact (L/M/H) | Status: Open / Mitigated / Closed

---

## Active Risks

| ID | Risk | P | I | Owner | Mitigation | Status |
|----|------|---|---|-------|------------|--------|
| R01 | YOLO generic COCO không detect biển số tốt | H | H | AI | Client-side crop + fallback chain; fine-tune plate model Sprint 1 | Open |
| R02 | EasyOCR chậm trên CPU, worker OOM | M | H | AI + DevOps | Resource limit 2G worker; warm-up; ONNX Sprint 4 | Open |
| R03 | Docker full stack không start được one-command | M | H | DevOps | Sprint 1 focus; healthchecks; wait-for-it script | Open |
| R04 | Frontend types lệch Backend schema | M | M | Frontend + Backend | Shared contract [`05-api-contracts.md`](05-api-contracts.md) | Open |
| R05 | Thiếu `alembic.ini` — migrate fail | H | M | Backend | Sprint 0 task; verify `make migrate` | Open |
| R06 | Dataset BR không đủ 100 ảnh test | M | H | AI | Augment + synthetic; minimum 50 MVP | Open |
| R07 | DVC model pull fail (Google Drive) | M | M | DevOps | Document manual download fallback | Open |
| R08 | ONNX accuracy drop > 5% vs PyTorch | M | M | AI | Benchmark gate; feature flag default off | Open |
| R09 | Không có auth — abuse upload local | L | L | Backend | Rate limit Sprint 5; file size cap | Open |
| R10 | README/docs lỗi thời gây onboarding chậm | M | M | All | Sprint 6 handoff doc; sync với code | Open |

---

## Technical Debt (Tracked)

| ID | Debt | Discovered | Plan to address |
|----|------|------------|-----------------|
| TD01 | S3/Supabase storage stub | Existing code | MinIO local Sprint 3 stretch |
| TD02 | Frontend missing NEEDS_REVIEW | Existing code | Sprint 2–4 frontend |
| TD03 | No automated tests | Existing code | Sprint 4–6 |
| TD04 | docker-compose app services commented | Existing code | Sprint 1 DevOps |
| TD05 | `RecognitionRequestCreate` empty schema | Existing code | Remove or implement Sprint 1 |

---

## Dependency Risks (Cross-Track)

| Blocker | Blocked track | Depends on | Sprint deadline |
|---------|---------------|------------|-----------------|
| `.env.example` master | Backend, Frontend | DevOps Sprint 0 | Sprint 0 Day 3 |
| `/health` endpoint | DevOps healthcheck | Backend Sprint 0 | Sprint 0 Day 5 |
| ML output JSON schema | Backend integration | AI Sprint 3 | Sprint 3 Day 7 |
| Model weights in `models/` | Backend worker | AI + DevOps Sprint 3 | Sprint 3 Day 10 |
| OpenAPI stable | Frontend client | Backend Sprint 1 | Sprint 1 Day 10 |
| Full docker stack | E2E tests | DevOps Sprint 1 | Sprint 3 |

---

## Mitigation Playbooks

### R01 — Poor plate detection

1. Sprint 0: Document current fallback in AI audit
2. Sprint 1: Client-side crop compensates (Frontend)
3. Sprint 1: Decision fine-tune vs heuristic (AI)
4. Sprint 3: Evaluate on test set; escalate if char accuracy < 80%

### R02 — Worker OOM / slow OCR

1. Set Docker memory limit 2G for worker
2. Lazy-load EasyOCR singleton at worker startup
3. First-request warm-up documented in runbook
4. Sprint 4: ONNX path for faster inference

### R03 — Docker startup failure

1. Sprint 0: infra-only compose verified
2. Sprint 1: Enable one service at a time (db → redis → app → worker → web)
3. `scripts/wait-for-it.sh` before app start
4. Document common errors in DevOps README

---

## Retrospective Log

| Sprint | Date | New risks | Closed | Actions |
|--------|------|-----------|--------|---------|
| 0 | — | — | — | — |
| 1 | — | — | — | — |
| 2 | — | — | — | — |
| 3 | — | — | — | — |
| 4 | — | — | — | — |
| 5 | — | — | — | — |
| 6 | — | — | — | — |

---

## Escalation Path

1. **Blocker > 4 hours:** Ghi vào `sprints/sprint-N-integration.md` → Daily standup
2. **Sprint goal at risk:** Track lead họp cross-team, defer stretch goals
3. **Critical (H/H):** Re-scope sprint, update [`01-vision-and-scope.md`](01-vision-and-scope.md) MVP table
