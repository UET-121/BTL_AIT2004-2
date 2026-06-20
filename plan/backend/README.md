# Backend Track — License Plate Recognition Redesign

## Scope

Nhánh Backend chịu trách nhiệm FastAPI REST API, SQLAlchemy models/migrations, Celery async worker, storage abstraction, ML pipeline integration (RecognitionService), và API hardening.

## Dependencies với các nhánh khác

| Nhánh | Backend cần từ họ | Backend cung cấp cho họ |
|-------|-------------------|------------------------|
| **DevOps** | DB/Redis compose, env template | `/health`, Dockerfiles |
| **AI Engineer** | ML output schema, model config | Worker task interface, DB storage |
| **Frontend** | — | REST API, OpenAPI spec |

## Sprint Files

| Sprint | File | Theme |
|--------|------|-------|
| 0 | [sprint-0-scaffold.md](sprint-0-scaffold.md) | FastAPI scaffold |
| 1 | [sprint-1-api-core.md](sprint-1-api-core.md) | CRUD API |
| 2 | [sprint-2-async-worker.md](sprint-2-async-worker.md) | Celery worker |
| 3 | [sprint-3-storage-db.md](sprint-3-storage-db.md) | Storage + reprocess |
| 4 | [sprint-4-ml-integration.md](sprint-4-ml-integration.md) | ML pipeline wire |
| 5 | [sprint-5-api-hardening.md](sprint-5-api-hardening.md) | Rate limit, tests |
| 6 | [sprint-6-integration-e2e.md](sprint-6-integration-e2e.md) | E2E + docs |

## Key Code Paths

| Component | Path |
|-----------|------|
| App entry | [`apps/api/app/main.py`](../../apps/api/app/main.py) |
| Routes | [`apps/api/app/api/routes.py`](../../apps/api/app/api/routes.py) |
| Models | [`apps/api/app/models/recognition.py`](../../apps/api/app/models/recognition.py) |
| Schemas | [`apps/api/app/models/schemas.py`](../../apps/api/app/models/schemas.py) |
| Config | [`apps/api/app/shared/config.py`](../../apps/api/app/shared/config.py) |
| Worker | [`apps/api/app/worker/tasks.py`](../../apps/api/app/worker/tasks.py) |
| Recognition | [`apps/api/app/services/recognition.py`](../../apps/api/app/services/recognition.py) |
| Storage | [`apps/api/app/services/storage.py`](../../apps/api/app/services/storage.py) |

## Related Docs

- [API contracts](../_shared/05-api-contracts.md)
- [Environment variables](../_shared/06-env-variables.md)
