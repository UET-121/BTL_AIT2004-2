# Sprint 0 — Foundation (Tuần 1–2)

**Dates:** 2026-06-23 → 2026-07-06

## Sprint Goal

Mọi dev clone repo và chạy được DB + Redis + API hello-world + Vite dev server.

## Cross-team Dependencies

| Task | Owner | Blocker for |
|------|-------|-------------|
| `.env.example` master | DevOps | Backend, Frontend |
| `alembic.ini` | Backend | DevOps migrate verification |
| API `/health` | Backend | DevOps Sprint 1 healthcheck |
| Vite proxy config | Frontend | Manual E2E test |
| `plan/_shared/06-env-variables.md` | DevOps | All tracks |
| Dataset directory structure | AI | Sprint 1 detection |

## Track Focus Summary

| Track | Key deliverables |
|-------|------------------|
| DevOps | docker-compose db/redis, Makefile root, wait-for-it.sh |
| AI | datasets/, labeling guide, model audit |
| Backend | FastAPI scaffold, CORS, alembic.ini, /health |
| Frontend | Vite scaffold, router, tailwind, types |

## Demo Script (Ngày 10)

1. Clone repo fresh
2. `cp .env.example .env` && `cp apps/api/.env.example apps/api/.env`
3. `make docker-up` → db + redis healthy (`docker compose ps`)
4. `cd apps/api && make migrate` → migrations apply
5. `make api` → `curl http://localhost:8000/health` → `{"status":"ok"}`
6. `cd apps/web && pnpm dev` → `http://localhost:5173` loads
7. Toggle dark mode → persists on reload
8. Open `http://localhost:8000/docs` → Swagger UI visible

## Definition of Done (Sprint 0)

- [ ] All 4 tracks: Sprint 0 checklists ≥ 80% complete
- [ ] No blockers for Sprint 1
- [ ] Risk register reviewed ([`07-risk-register.md`](../_shared/07-risk-register.md))
- [ ] R05 (alembic.ini) closed

## Blockers Log

| Date | Blocker | Owner | Resolution |
|------|---------|-------|------------|
| | | | |

## Retrospective Notes

_Action items for Sprint 1 — fill after retro_
