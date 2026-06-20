# Definition of Done (DoD) — Shared Across All Tracks

Áp dụng cho mọi task/story trong 4 nhánh: DevOps, AI Engineer, Backend, Frontend.

## Story-Level DoD

Một story được coi là **Done** khi tất cả điều kiện sau đạt:

### Code & Implementation

- [ ] Code merged vào branch chính của sprint (hoặc feature branch đã review)
- [ ] Tuân thủ conventions hiện có của repo (naming, layout, import style)
- [ ] Không có hardcoded secrets, credentials, hoặc API keys
- [ ] Không commit file generated không cần thiết (`__pycache__`, `node_modules`, `.env`)
- [ ] Diff tập trung vào scope story — không refactor không liên quan

### Testing

- [ ] Unit test cho logic mới (Backend, AI) hoặc component test (Frontend) nếu applicable
- [ ] Manual test theo steps trong sprint checklist đã pass
- [ ] Không regression: smoke test (`scripts/smoke-test.sh`) pass nếu đã có
- [ ] Migration (nếu có): `alembic upgrade head` và `downgrade -1` verified

### Documentation

- [ ] README hoặc inline doc cập nhật nếu thay đổi API, env vars, hoặc workflow
- [ ] Env vars mới thêm vào [`06-env-variables.md`](06-env-variables.md) và `.env.example`
- [ ] Sprint checklist item marked `[x]` trong file sprint tương ứng

### Review & Integration

- [ ] Code review bởi ít nhất 1 thành viên nhánh khác (cross-track nếu touch integration point)
- [ ] Không blocker mở trong [`sprints/sprint-N-integration.md`](../sprints/)
- [ ] CI script (`scripts/ci.sh`) pass — khi CI đã setup (Sprint 4+)

## Sprint-Level DoD

Một sprint được coi là **Done** khi:

- [ ] Sprint Goal (trong `sprints/sprint-N-integration.md`) đạt được
- [ ] ≥ 80% checklist items hoàn thành trên mỗi nhánh
- [ ] Demo script chạy thành công trong Sprint Review (Ngày 10)
- [ ] Không critical/high bug mở liên quan sprint goal
- [ ] Risk register reviewed và cập nhật
- [ ] Retrospective action items ghi nhận cho sprint tiếp

## Release-Level DoD (Sprint 6 / v1.0)

- [ ] Full stack `docker compose up -d` → 5 services healthy < 3 phút
- [ ] Char accuracy ≥ 90% trên frozen test set (100 images)
- [ ] Review rate ≤ 25%
- [ ] Backend pytest coverage ≥ 70%
- [ ] Frontend Playwright E2E pass
- [ ] Performance baseline documented (p50/p95 latency)
- [ ] Onboarding doc: dev mới setup trong ≤ 30 phút
- [ ] CHANGELOG + version tag
- [ ] All migration files applied cleanly on fresh DB

## Track-Specific Additions

### DevOps

- [ ] Docker service có healthcheck
- [ ] Script mới có `--help` hoặc comment header
- [ ] Volume paths dùng `./data/` (gitignored)

### AI Engineer

- [ ] Model metrics ghi trong MODEL_CARD hoặc evaluation CSV
- [ ] Notebook có kernel metadata và chạy top-to-bottom không lỗi
- [ ] Không commit raw dataset lớn — dùng DVC hoặc gitignore

### Backend

- [ ] Endpoint có OpenAPI schema đúng
- [ ] Error responses dùng consistent schema `{detail: string}`
- [ ] Async/sync boundary rõ ràng trong worker

### Frontend

- [ ] TypeScript strict — không `any` mới không justified
- [ ] Responsive trên viewport ≥ 375px
- [ ] Loading và error states implemented
- [ ] Dark mode compatible

## Checklist Template (Copy per Story)

```markdown
## Story: [Title]

- [ ] Implementation complete
- [ ] Tests pass (unit/manual/smoke)
- [ ] Docs/env updated if needed
- [ ] Code reviewed
- [ ] Sprint integration unblocked
- [ ] Checklist item marked in sprint file
```
