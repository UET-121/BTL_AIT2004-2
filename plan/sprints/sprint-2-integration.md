# Sprint 2 — Async & Storage (Tuần 5–6)

**Dates:** 2026-07-21 → 2026-08-03

## Sprint Goal

Upload → async processing → plate result hiển thị trên UI; observability basics in place.

## Cross-team Dependencies

| Task | Owner | Blocker for |
|------|-------|-------------|
| Celery worker + task | Backend | Async processing |
| RecognitionService stub | Backend | Worker produces results |
| EasyOCR + preprocessing tuned | AI | Meaningful plate results |
| Extended /health | Backend + DevOps | Smoke test |
| RequestList + polling | Frontend | Live status updates |
| smoke-test.sh | DevOps | Automated verification |

## Track Focus Summary

| Track | Key deliverables |
|-------|------------------|
| DevOps | Structured logging, smoke test, Flower (dev) |
| AI | OCR/preprocessing pipeline, A/B test |
| Backend | Celery task, migrations 002-003, status lifecycle |
| Frontend | Request list, status badges, auto-refresh |

## Demo Script (Ngày 10)

1. `./scripts/smoke-test.sh` → passes (health + upload + poll)
2. Open home page → upload image
3. List shows PENDING status with yellow badge
4. Within 30s → status changes to COMPLETED (or NEEDS_REVIEW/FAILED)
5. Click row → detail page shows plate_number
6. Show JSON logs with request_id correlation
7. Flower dashboard at `:5555` shows completed task (dev profile)

## Definition of Done (Sprint 2)

- [ ] End-to-end upload → plate result works
- [ ] Smoke test script passes
- [ ] Frontend list auto-refreshes
- [ ] NEEDS_REVIEW status in frontend types

## Blockers Log

| Date | Blocker | Owner | Resolution |
|------|---------|-------|------------|
| | | | |

## Retrospective Notes

_Action items for Sprint 3_
