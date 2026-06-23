# Plan — License Plate Recognition Redesign

Tài liệu Agile redesign cho dự án **License Plate Recognition** — 12 tuần, 6 sprint, 4 nhánh song song.

**Deploy target:** Local + Docker Compose  
**Start date:** 2026-06-23  
**Release target:** v1.0 — 2026-09-28

---

## Mục lục

### Shared (Cross-team)

| Doc | Mô tả |
|-----|-------|
| [01-vision-and-scope.md](_shared/01-vision-and-scope.md) | Product vision, personas, MVP vs v1.0 |
| [02-target-architecture.md](_shared/02-target-architecture.md) | Kiến trúc mục tiêu, data model, pipeline |
| [03-definition-of-done.md](_shared/03-definition-of-done.md) | DoD story / sprint / release |
| [04-sprint-calendar.md](_shared/04-sprint-calendar.md) | Timeline, milestones, ceremonies |
| [05-api-contracts.md](_shared/05-api-contracts.md) | REST API spec, Celery schema, TS types |
| [06-env-variables.md](_shared/06-env-variables.md) | Master env reference |
| [07-risk-register.md](_shared/07-risk-register.md) | Rủi ro cross-team + mitigation |

### Track Plans (4 nhánh)

| Nhánh | README | Sprints |
|-------|--------|---------|
| **DevOps** | [devops/README.md](devops/README.md) | sprint-0 → sprint-6 |
| **AI Engineer** | [ai-engineer/README.md](ai-engineer/README.md) | sprint-0 → sprint-6 |
| **Backend** | [backend/README.md](backend/README.md) | sprint-0 → sprint-6 |
| **Frontend** | [frontend/README.md](frontend/README.md) | sprint-0 → sprint-6 |

### Sprint Integration (Cross-team view)

| Sprint | Theme | File |
|--------|-------|------|
| 0 | Foundation | [sprints/sprint-0-integration.md](sprints/sprint-0-integration.md) |
| 1 | Core Features | [sprints/sprint-1-integration.md](sprints/sprint-1-integration.md) |
| 2 | Async & Storage | [sprints/sprint-2-integration.md](sprints/sprint-2-integration.md) |
| 3 | ML Integration | [sprints/sprint-3-integration.md](sprints/sprint-3-integration.md) |
| 4 | Quality & ONNX | [sprints/sprint-4-integration.md](sprints/sprint-4-integration.md) |
| 5 | Hardening | [sprints/sprint-5-integration.md](sprints/sprint-5-integration.md) |
| 6 | Release | [sprints/sprint-6-integration.md](sprints/sprint-6-integration.md) |

---

## Quy trình Agile

### Sprint Structure

- **Duration:** 2 tuần (10 ngày làm việc)
- **Total:** 6 sprint = 12 tuần

### Ceremonies

| Ceremony | When | Duration | Output |
|----------|------|----------|--------|
| **Sprint Planning** | Ngày 1 (Mon) | 2h | Backlog committed per track |
| **Daily Standup** | Hàng ngày 9:30 | 15min | Blockers → sprint integration file |
| **Backlog Refinement** | Ngày 5 | 1h | Next sprint prep |
| **Sprint Review** | Ngày 10 (Fri w2) | 1h | Demo theo script trong `sprints/` |
| **Retrospective** | Sau Review | 45min | Action items → risk register |

### Workflow

1. **Planning:** Mỗi track lead chọn tasks từ `sprint-N-*.md` checklist
2. **Daily:** Update blockers trong `sprints/sprint-N-integration.md`
3. **Review:** Chạy demo script cross-team
4. **Retro:** Cập nhật [`07-risk-register.md`](_shared/07-risk-register.md)
5. **DoD:** Mark `[x]` trên checklist khi story done ([`03-definition-of-done.md`](_shared/03-definition-of-done.md))

---

## RACI Matrix

| Hạng mục | DevOps | AI | Backend | Frontend |
|----------|--------|-----|---------|----------|
| Docker Compose full stack | **R/A** | C | C | C |
| ML model & pipeline | C | **R/A** | I | I |
| REST API contracts | C | C | **R/A** | C |
| UI/UX flows | I | C | C | **R/A** |
| `.env.example` master | **A** | C | C | C |
| CI / pre-commit | **R/A** | I | C | C |
| Test set & evaluation | C | **R/A** | I | I |
| E2E tests | C | I | R | **R/A** |

**Legend:** R = Responsible, A = Accountable, C = Consulted, I = Informed

---

## Timeline

```
Sprint 0  [2026-06-23 ─ 2026-07-06]  Foundation
Sprint 1  [2026-07-07 ─ 2026-07-20]  Core Features
Sprint 2  [2026-07-21 ─ 2026-08-03]  Storage & Real-time (MinIO)
Sprint 3  [2026-08-04 ─ 2026-08-17]  ML Integration (YOLO & OCR)
Sprint 4  [2026-08-18 ─ 2026-08-31]  Quality & ONNX Runtime
Sprint 5  [2026-09-01 ─ 2026-09-14]  Hardening
Sprint 6  [2026-09-15 ─ 2026-09-28]  Release v1.0
```

Chi tiết milestones: [`04-sprint-calendar.md`](_shared/04-sprint-calendar.md)

---

## Cách sử dụng plan này

### Cho track lead

1. Mở README của nhánh (vd. [`devops/README.md`](devops/README.md))
2. Mỗi sprint, làm theo checklist trong `sprint-N-*.md`
3. Mark `[ ]` → `[x]` khi task done
4. Báo blockers trong daily → ghi vào `sprints/sprint-N-integration.md`

### Cho dev mới

1. Đọc [`01-vision-and-scope.md`](_shared/01-vision-and-scope.md) — hiểu big picture
2. Đọc [`02-target-architecture.md`](_shared/02-target-architecture.md) — hiểu kiến trúc
3. Chọn nhánh → đọc README + sprint hiện tại
4. Setup env: [`06-env-variables.md`](_shared/06-env-variables.md)

### Cho sprint review

1. Mở `sprints/sprint-N-integration.md`
2. Chạy demo script
3. Verify Definition of Done
4. Cập nhật risk register nếu cần

---

## Mapping: Plan → Code hiện tại

| Plan area | Reuse | Rebuild/improve |
|-----------|-------|-----------------|
| Backend API | routes, models, config | alembic.ini, tests, MinIO integration |
| AI pipeline | preprocessing, validation, EasyOCR | Plate YOLO, ONNX inference, Stream processing |
| Frontend | Upload, stream display, logs | Confidence UI, NEEDS_REVIEW, bbox, WebSockets |
| DevOps | docker-compose db/minio, Dockerfiles | Full stack compose, CI, resource limit |

---

## v1.0 Release Criteria

- [ ] `docker compose up -d` → 5 services healthy < 3 phút
- [ ] Char accuracy ≥ 90% (100-image test set)
- [ ] Review rate ≤ 25%
- [ ] Backend coverage ≥ 70%
- [ ] Playwright E2E pass
- [ ] Onboarding ≤ 30 phút
- [ ] Git tag v1.0.0

---

## Liên hệ & Escalation

- **Blocker > 4h:** Ghi `sprints/sprint-N-integration.md` → escalate at standup
- **Sprint goal at risk:** Cross-team sync, defer stretch goals
- **Critical risk (H/H):** Xem [`07-risk-register.md`](_shared/07-risk-register.md) escalation path
