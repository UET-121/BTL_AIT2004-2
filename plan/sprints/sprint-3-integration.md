# Sprint 3 — ML Integration (Tuần 7–8)

**Dates:** 2026-08-04 → 2026-08-17

## Sprint Goal

Full ML pipeline integrated; confidence scores stored; Docker full stack stable; detail page shows confidence.

## Cross-team Dependencies

| Task | Owner | Blocker for |
|------|-------|-------------|
| Confidence scoring formula | AI | Backend status mapping |
| ML output JSON schema | AI | Backend DB storage |
| RecognitionService wired | Backend | Real ML results |
| models/ volume mount | DevOps | Worker model loading |
| Reprocess endpoint | Backend | Frontend Sprint 4 prep |
| Confidence UI + bbox | Frontend | User sees ML quality |
| Storage LocalStorage | Backend | Upload persistence |

## Track Focus Summary

| Track | Key deliverables |
|-------|------------------|
| DevOps | models/ layout, DVC docs, volume mounts |
| AI | BR validation, confidence tuning, output schema |
| Backend | Storage, reprocess, ML integration start |
| Frontend | Detail page, confidence, bbox overlay |

## Demo Script (Ngày 10)

1. `make models` → weights pulled
2. `docker compose up -d` → all services healthy
3. Upload clear plate image → COMPLETED with high confidence (green bar)
4. Upload blurry image → NEEDS_REVIEW with orange warning
5. Detail page shows: confidence breakdown, bounding box on image
6. Click reprocess on NEEDS_REVIEW → new attempt
7. Show API response JSON with all metadata fields

## Definition of Done (Sprint 3)

- [ ] Confidence fields populated end-to-end
- [ ] Bbox overlay renders correctly
- [ ] Reprocess API works
- [ ] Model artifacts in models/ directory

## Blockers Log

| Date | Blocker | Owner | Resolution |
|------|---------|-------|------------|
| | | | |

## Retrospective Notes

_Action items for Sprint 4_
