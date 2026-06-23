# Backend Track — License Plate Recognition Redesign

## Scope

Nhánh Backend chịu trách nhiệm thiết kế FastAPI REST API, kết nối cơ sở dữ liệu SQLAlchemy models/migrations (PostgreSQL), tích hợp lưu trữ tệp tin (MinIO/Local Storage), quản lý kết nối thời gian thực WebSockets để phát frame nhận diện, và viết tích hợp kiểm thử (integration tests).

## Dependencies với các nhánh khác

| Nhánh | Backend cần từ họ | Backend cung cấp cho họ |
|-------|-------------------|------------------------|
| **DevOps** | DB/MinIO compose, env template | Dockerfile stable |
| **AI Engineer** | ONNX Model path, input/output format | API Router & DB models |
| **Frontend** | — | REST API & WebSocket specification |

## Sprint Files

| Sprint | File | Theme |
|--------|------|-------|
| 0 | [sprint-0-scaffold.md](sprint-0-scaffold.md) | FastAPI scaffold |
| 1 | [sprint-1-api-core.md](sprint-1-api-core.md) | CRUD API |
| 2 | [sprint-2-async-worker.md](sprint-2-async-worker.md) | WebSocket & Real-time setup |
| 3 | [sprint-3-storage-db.md](sprint-3-storage-db.md) | MinIO storage + DB integrations |
| 4 | [sprint-4-ml-integration.md](sprint-4-ml-integration.md) | YOLOv8 ONNX runtime integration |
| 5 | [sprint-5-api-hardening.md](sprint-5-api-hardening.md) | Optimization & Tests |
| 6 | [sprint-6-integration-e2e.md](sprint-6-integration-e2e.md) | E2E + docs |

## Key Code Paths

| Component | Path |
|-----------|------|
| App entry | [`apps/api/app/main.py`](../../apps/api/app/main.py) |
| Routes | [`apps/api/app/api/routes.py`](../../apps/api/app/api/routes.py) |
| Models | [`apps/api/app/models/recognition.py`](../../apps/api/app/models/recognition.py) |
| Schemas | [`apps/api/app/models/schemas.py`](../../apps/api/app/models/schemas.py) |
| Config | [`apps/api/app/shared/config.py`](../../apps/api/app/shared/config.py) |
| Database | [`apps/api/app/shared/database.py`](../../apps/api/app/shared/database.py) |
| Real-time Manager | [`apps/api/app/realtime/manager.py`](../../apps/api/app/realtime/manager.py) |
| Real-time Inference | [`apps/api/app/realtime/inference.py`](../../apps/api/app/realtime/inference.py) |
| Storage | [`apps/api/app/services/storage.py`](../../apps/api/app/services/storage.py) |

## Related Docs

- [API contracts](../_shared/05-api-contracts.md)
- [Environment variables](../_shared/06-env-variables.md)
