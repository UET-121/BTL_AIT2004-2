# Vision & Scope — License Plate Recognition Redesign

## Product Vision

Xây dựng hệ thống nhận dạng biển số xe Brazil (Mercosul + định dạng cũ) end-to-end: người dùng upload ảnh qua web, hệ thống xử lý bất đồng bộ qua pipeline ML (detection → preprocessing → OCR → validation), trả kết quả kèm confidence score và flag cần review thủ công khi độ tin cậy thấp.

## Problem Statement

Dự án hiện tại đã có monorepo hoạt động (`apps/api` + `apps/web`) nhưng còn nhiều gap:

- Infrastructure chưa hoàn chỉnh (Docker Compose chỉ chạy DB/Redis)
- ML pipeline dùng model YOLO generic COCO, chưa tối ưu cho biển số
- Frontend thiếu hiển thị confidence, bounding box, trạng thái `NEEDS_REVIEW`
- Không có test/CI, documentation lỗi thời
- ONNX export tồn tại nhưng chưa tích hợp inference

## Personas

| Persona | Mô tả | Nhu cầu chính |
|---------|-------|---------------|
| **Operator** | Nhân viên vận hành bãi xe / cổng | Upload nhanh, xem kết quả rõ ràng, retry khi lỗi |
| **Reviewer** | Người duyệt kết quả nghi ngờ | Danh sách `NEEDS_REVIEW`, xem raw OCR vs corrected, reprocess |
| **Developer** | Dev full-stack / ML | Clone → chạy 1 lệnh, docs chính xác, test coverage |
| **DevOps** | Vận hành local/staging | Docker Compose ổn định, healthcheck, backup, CI |

## Scope — In Scope (v1.0)

- [ ] Nhận dạng biển số Brazil (Mercosul `ABC1D23`, old `ABC1234`)
- [ ] Upload ảnh JPEG/PNG qua web UI (drag-drop + crop)
- [ ] Xử lý async qua Celery + Redis
- [ ] Lưu trữ local (default) hoặc MinIO (stretch)
- [ ] Confidence scoring + auto flag `NEEDS_REVIEW`
- [ ] Reprocess request FAILED / NEEDS_REVIEW
- [ ] Chạy full stack trên Local + Docker Compose
- [ ] ONNX inference (optional, feature flag)
- [ ] Test coverage ≥ 70% backend, E2E Playwright frontend

## Scope — Out of Scope (v1.0)

- Authentication / multi-tenant
- Cloud deploy (GCP/AWS) — chỉ document hướng dẫn tương lai
- Multi-region plates (VN, US, EU)
- Mobile app native
- Real-time video stream LPR
- Active learning loop tự động

## MVP vs v1.0

### MVP (Sprint 0–3, Tuần 1–8)

| Feature | MVP | v1.0 |
|---------|-----|------|
| Upload + list + detail | Yes | Yes |
| Celery async processing | Yes | Yes |
| EasyOCR + BR validation | Yes | Yes |
| Client-side crop | Yes | Yes |
| YOLO plate-specific model | Heuristic fallback | Fine-tuned or improved |
| Confidence UI | Basic badge | Full breakdown + bbox overlay |
| Docker full stack | Partial | Complete |
| Tests | Smoke only | Full suite |
| ONNX inference | No | Yes (feature flag) |

### v1.0 Release Criteria (Sprint 6)

- [ ] `docker compose up -d` → 5 services healthy < 3 phút
- [ ] Char accuracy ≥ 90% trên test set 100 ảnh
- [ ] Review rate ≤ 25%
- [ ] Upload → result p95 latency < 30s (local)
- [ ] Onboarding doc: dev mới chạy được trong 30 phút
- [ ] Zero critical bugs trong sprint review

## Success Metrics

| Metric | Target |
|--------|--------|
| Char accuracy (test set) | ≥ 90% |
| Review rate | ≤ 25% |
| API uptime (local docker) | 99% trong demo window |
| p95 upload-to-result latency | < 30s |
| Backend test coverage | ≥ 70% |
| Lighthouse performance (frontend) | ≥ 85 |

## Assumptions & Constraints

- **Timeline:** 12 tuần (6 sprint × 2 tuần), bắt đầu 2026-06-23
- **Deploy target:** Local + Docker Compose (không cloud production)
- **Team:** 4 nhánh song song (DevOps, AI, Backend, Frontend)
- **Reuse:** Học từ code hiện tại, không rewrite blind
- **Language:** UI tiếng Anh/PT-BR; docs plan tiếng Việt

## References

- Code hiện tại: [`apps/api`](../../apps/api), [`apps/web`](../../apps/web)
- Root README: [`README.md`](../../README.md)
- Sprint calendar: [`04-sprint-calendar.md`](04-sprint-calendar.md)
