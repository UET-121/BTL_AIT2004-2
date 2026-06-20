# Sprint 4 — Quality & ONNX (Tuần 9–10)

**Dates:** 2026-08-18 → 2026-08-31

## Sprint Goal

CI green; ONNX inference available; review workflow complete; pre-commit hooks active.

## Cross-team Dependencies

| Task | Owner | Blocker for |
|------|-------|-------------|
| ONNX detector + export | AI | Feature flag testing |
| Integration tests | Backend | CI script |
| pre-commit + ci.sh | DevOps | Quality gates |
| Review UI + reprocess fix | Frontend | NEEDS_REVIEW workflow |
| USE_ONNX_INFERENCE env | Backend + DevOps | ONNX mode testing |

## Track Focus Summary

| Track | Key deliverables |
|-------|------------------|
| DevOps | pre-commit, ci.sh, docker build cache |
| AI | ONNX export/inference, MODEL_CARD, benchmark |
| Backend | Full ML integration, integration tests |
| Frontend | Review workflow, reprocess for NEEDS_REVIEW |

## Demo Script (Ngày 10)

1. `make ci` → all checks pass (lint, test, build)
2. Upload image with PyTorch mode → result
3. Set `USE_ONNX_INFERENCE=true` → restart worker → same image → compare result
4. Show NEEDS_REVIEW banner + reprocess flow
5. Show MODEL_CARD.md metrics
6. Show ONNX benchmark CSV (latency comparison)
7. Pre-commit hook blocks bad commit demo (optional)

## Definition of Done (Sprint 4)

- [ ] `make ci` green
- [ ] ONNX feature flag works
- [ ] Review + reprocess UI complete
- [ ] Integration tests pass

## Blockers Log

| Date | Blocker | Owner | Resolution |
|------|---------|-------|------------|
| | | | |

## Retrospective Notes

_Action items for Sprint 5_
