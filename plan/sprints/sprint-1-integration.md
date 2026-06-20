# Sprint 1 — Core Features (Tuần 3–4)

**Dates:** 2026-07-07 → 2026-07-20

## Sprint Goal

User upload ảnh → request xuất hiện trong DB; Docker full stack khởi động được; detection strategy decided.

## Cross-team Dependencies

| Task | Owner | Blocker for |
|------|-------|-------------|
| POST /api/v1/recognition | Backend | Frontend upload |
| Docker app/worker/web services | DevOps | Full stack demo |
| Detection strategy decision | AI | Backend ML Sprint 4 prep |
| LocalStorage save | Backend | Frontend upload success |
| ImageUpload + Cropper | Frontend | Demo upload flow |

## Track Focus Summary

| Track | Key deliverables |
|-------|------------------|
| DevOps | 5-service docker-compose, Dockerfiles fixed |
| AI | YOLO detector, fallback chain, detection strategy doc |
| Backend | CRUD API, migration 001, upload endpoint |
| Frontend | Upload flow, cropper, detail stub |

## Demo Script (Ngày 10)

1. `docker compose up -d --build` → 5 services healthy
2. Open `http://localhost` → React app loads via nginx
3. Upload plate image → crop region → submit
4. Redirected to detail page showing request ID and NOT_STARTED status
5. `curl http://localhost:8000/api/v1/recognition` → list includes new request
6. Worker logs show task picked up (PENDING) — full result Sprint 2
7. Show Swagger docs with all 3 GET/POST endpoints

## Definition of Done (Sprint 1)

- [ ] Upload → DB record created
- [ ] Docker 5 services start < 3 min
- [ ] Detection strategy documented
- [ ] All track Sprint 1 checklists ≥ 80% complete

## Blockers Log

| Date | Blocker | Owner | Resolution |
|------|---------|-------|------------|
| | | | |

## Retrospective Notes

_Action items for Sprint 2_
