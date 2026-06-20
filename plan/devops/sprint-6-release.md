# Sprint 6 — Release (Tuần 13–14)

**Dates:** 2026-09-15 → 2026-09-28  
**Sprint Goal:** v1.0 release checklist, performance baseline, onboarding handoff doc.

---

## 1. Release Checklist (Ngày 1–3)

- [ ] **Tạo `plan/devops/RELEASE-CHECKLIST.md`:**
  - [ ] All 6 sprint integration DoD met
  - [ ] `make ci` green
  - [ ] `make smoke-test` green against prod profile
  - [ ] Migrations applied on fresh DB
  - [ ] Model artifacts in `models/release/v1.0/`
  - [ ] No critical/high open bugs
  - [ ] README updated
- [ ] **Version tag:** `git tag v1.0.0` with annotated message
- [ ] **CHANGELOG.md:** Summarize all sprints, breaking changes, known issues
- [ ] **Migration run order doc:** List migrations 001→003, verify on empty DB

## 2. Production Profile Finalization (Ngày 3–4)

- [ ] **`docker compose --profile prod up -d`:** Final config review
- [ ] **Remove dev artifacts:** No `--reload`, no debug ports, no Flower
- [ ] **nginx only for frontend:** No Vite dev server reference in prod docs
- [ ] **Env template for prod-like:** `.env.prod.example` with safe defaults
- [ ] **Startup time benchmark:** Record cold start → all healthy

## 3. Performance Baseline (Ngày 4–6)

- [ ] **Tạo `plan/devops/PERFORMANCE-BASELINE.md`:**
  - [ ] **Upload → COMPLETED latency:** Run 20 uploads, record p50, p95, p99
  - [ ] **API response times:** GET list, GET detail — p95 < 200ms
  - [ ] **Worker throughput:** Tasks/minute with concurrency=1
  - [ ] **Docker resource usage:** Peak memory per service during load
  - [ ] **Cold start time:** Worker first task (model load) vs warm tasks
- [ ] **Load test coordination:** Use Backend locust script (10 concurrent)
- [ ] **Hardware spec:** Document machine used for benchmark (CPU, RAM, OS)
- [ ] **Acceptance:** p95 upload-to-result < 30s on reference hardware

## 4. Onboarding Handoff Doc (Ngày 6–8)

- [ ] **Tạo `plan/devops/ONBOARDING.md`:** 30-minute new dev guide
  - [ ] **Minute 0–5:** Prerequisites install (Docker, Python, Node, pnpm)
  - [ ] **Minute 5–10:** Clone, copy env files, `make docker-up`
  - [ ] **Minute 10–15:** `make models`, `make migrate`
  - [ ] **Minute 15–20:** Start full stack, verify `/health`
  - [ ] **Minute 20–25:** Open web UI, upload test image
  - [ ] **Minute 25–30:** Run smoke test, read plan/README
- [ ] **Troubleshooting FAQ:** Top 10 issues from retrospectives
- [ ] **Architecture diagram link:** Point to `_shared/02-target-architecture.md`
- [ ] **Team contacts / RACI:** Who owns what track

## 5. Final Documentation Sync (Ngày 8–9)

- [ ] **Update root README.md:** Correct paths (`apps/api`, `apps/web`), all endpoints, env vars
- [ ] **Remove stale references:** Old `app/` flat structure, missing files
- [ ] **Docker services table:** All 5 services with ports and purpose
- [ ] **Verify all doc links work:** No broken relative links in plan/

## 6. Release Demo Preparation (Ngày 9–10)

- [ ] **Demo script rehearsal:** Full flow from [`sprint-6-integration.md`](../sprints/sprint-6-integration.md)
- [ ] **Clean environment test:** Fresh clone on clean machine (or VM)
- [ ] **Record demo video (optional):** 5-min walkthrough for stakeholders
- [ ] **Post-release monitoring plan:** What to watch first 48 hours (logs, disk, memory)
- [ ] **v1.1 backlog seed:** Collect stretch items deferred from all sprints

---

## Deliverables

| Artifact | Path |
|----------|------|
| Release checklist | `plan/devops/RELEASE-CHECKLIST.md` |
| Performance baseline | `plan/devops/PERFORMANCE-BASELINE.md` |
| Onboarding guide | `plan/devops/ONBOARDING.md` |
| CHANGELOG | `CHANGELOG.md` |
| Git tag | `v1.0.0` |

## Release Sign-off

| Criteria | Status |
|----------|--------|
| Full stack docker healthy < 3 min | [ ] |
| Char accuracy ≥ 90% | [ ] |
| Smoke test pass | [ ] |
| CI green | [ ] |
| Onboarding ≤ 30 min verified | [ ] |
| All track leads sign off | [ ] |

## Post-Release

- [ ] **Archive sprint plans:** Mark all sprint checklists with final status
- [ ] **Retrospective final:** Lessons learned doc
- [ ] **Re-index GitNexus:** `npx gitnexus analyze` after release commit
