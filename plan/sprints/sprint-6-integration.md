# Sprint 6 — Release (Tuần 13–14)

**Dates:** 2026-09-15 → 2026-09-28

## Sprint Goal

v1.0 release: E2E tests pass, documentation complete, performance baseline recorded, 30-min onboarding verified.

## Cross-team Dependencies

| Task | Owner | Blocker for |
|------|-------|-------------|
| Release bundle models/release/v1.0/ | AI | v1.0 sign-off |
| E2E tests (backend + frontend) | Backend + Frontend | Release gate |
| RELEASE-CHECKLIST.md | DevOps | Final release |
| ONBOARDING.md 30-min test | DevOps | Handoff |
| README sync | Backend | Accurate docs |
| Playwright E2E | Frontend | QA sign-off |
| PERFORMANCE-BASELINE.md | DevOps + Backend | Release metrics |

## Track Focus Summary

| Track | Key deliverables |
|-------|------------------|
| DevOps | Release checklist, onboarding, performance baseline, v1.0 tag |
| AI | Model handoff, runbook, integration test 10/10 |
| Backend | E2E script, load test, OpenAPI export, README |
| Frontend | Playwright tests, Lighthouse, browser matrix |

## Demo Script (Ngày 10 — Release Review)

1. **Fresh onboarding test (30 min):** New team member follows ONBOARDING.md
2. `docker compose --profile prod up -d` → all healthy < 3 min
3. `make ci` → green
4. `make smoke-test` → green
5. `pnpm test:e2e` (Playwright) → green
6. **Live demo:** Upload → crop → COMPLETED with confidence + bbox
7. **Review demo:** NEEDS_REVIEW → reprocess → new result
8. **Metrics presentation:**
   - Char accuracy: ___%
   - Review rate: ___%
   - p95 latency: ___s
9. Show `models/release/v1.0/` bundle
10. Show CHANGELOG.md + git tag v1.0.0

## Definition of Done (Sprint 6 / v1.0)

- [ ] All 6 sprint integration DoD met across tracks
- [ ] Release checklist 100% complete
- [ ] E2E + smoke + CI all green
- [ ] Onboarding verified ≤ 30 minutes
- [ ] All track leads sign off
- [ ] Git tag v1.0.0 created
- [ ] Retrospective final + v1.1 backlog seeded

## Release Sign-off

| Reviewer | Track | Approved | Date |
|----------|-------|----------|------|
| | DevOps | [ ] | |
| | AI Engineer | [ ] | |
| | Backend | [ ] | |
| | Frontend | [ ] | |
| | Product Owner | [ ] | |

## v1.0 Metrics (Fill at Release)

| Metric | Target | Actual |
|--------|--------|--------|
| Char accuracy | ≥ 90% | |
| Review rate | ≤ 25% | |
| p95 upload-to-result | < 30s | |
| Backend coverage | ≥ 70% | |
| Lighthouse performance | ≥ 85 | |
| Docker startup | < 3 min | |
| Onboarding time | ≤ 30 min | |

## Blockers Log

| Date | Blocker | Owner | Resolution |
|------|---------|-------|------------|
| | | | |

## Final Retrospective

_Project-wide lessons learned — fill after release_

## v1.1 Backlog Seeds

_Collect from all track ROADMAP docs_
