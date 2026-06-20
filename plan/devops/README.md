# DevOps Track — License Plate Recognition Redesign

## Scope

Nhánh DevOps chịu trách nhiệm infrastructure, Docker Compose, CI/CD local, observability, model artifact management, backup/disaster recovery, và release process.

**Deploy target:** Local + Docker Compose (không cloud production trong v1.0).

## Dependencies với các nhánh khác

| Nhánh | DevOps cần từ họ | DevOps cung cấp cho họ |
|-------|------------------|------------------------|
| **Backend** | `/health` endpoint, Dockerfile stable | DB/Redis compose, env template |
| **Frontend** | Dockerfile build success | nginx proxy config, web service |
| **AI Engineer** | Model paths, env vars | `models/` layout, DVC docs, volume mounts |

## Sprint Files

| Sprint | File | Theme |
|--------|------|-------|
| 0 | [sprint-0-foundation.md](sprint-0-foundation.md) | Monorepo, db/redis compose |
| 1 | [sprint-1-local-stack.md](sprint-1-local-stack.md) | Full 5-service stack |
| 2 | [sprint-2-observability.md](sprint-2-observability.md) | Logging, health, smoke test |
| 3 | [sprint-3-model-artifacts.md](sprint-3-model-artifacts.md) | DVC, models/, ONNX volume |
| 4 | [sprint-4-quality-gates.md](sprint-4-quality-gates.md) | Pre-commit, CI script |
| 5 | [sprint-5-hardening.md](sprint-5-hardening.md) | Resource limits, backup |
| 6 | [sprint-6-release.md](sprint-6-release.md) | Release checklist, handoff |

## Dev Workflow (Target)

```bash
# 1. Start infrastructure
make docker-up          # hoặc: docker compose up -d db redis

# 2. Pull models (khi cần)
make models             # dvc pull

# 3. Run migrations
cd apps/api && make migrate

# 4. Start app (2 terminals) hoặc full docker
make api                # terminal 1
make worker             # terminal 2
# hoặc
docker compose up -d    # all services

# 5. Frontend dev
cd apps/web && pnpm dev

# 6. Smoke test
./scripts/smoke-test.sh
```

## Key Files (Target State)

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Production-like stack |
| `docker-compose.dev.yml` | Hot reload overlay |
| `docker-compose.override.yml.example` | Local mount template |
| `Makefile` (root) | Wrapper commands |
| `scripts/wait-for-it.sh` | Wait for healthy deps |
| `scripts/smoke-test.sh` | End-to-end smoke |
| `scripts/ci.sh` | Local CI pipeline |
| `scripts/backup-db.sh` | PostgreSQL backup |
| `.pre-commit-config.yaml` | Lint hooks |

## RACI

| Task | DevOps | AI | Backend | Frontend |
|------|--------|-----|---------|----------|
| Docker Compose full stack | **R/A** | C | C | C |
| `.env.example` master | **A** | C | C | C |
| CI/pre-commit | **R/A** | I | C | C |
| Model artifact storage | **R** | **A** | I | I |
| nginx config | **R** | I | C | C |

## Related Docs

- [Environment variables](../_shared/06-env-variables.md)
- [Target architecture](../_shared/02-target-architecture.md)
- [Risk register](../_shared/07-risk-register.md)
