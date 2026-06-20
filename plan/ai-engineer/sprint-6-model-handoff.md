# Sprint 6 — Model Handoff (Tuần 13–14)

**Dates:** 2026-09-15 → 2026-09-28  
**Sprint Goal:** Release bundle packaged, integration verified, runbook delivered, v1.0 AI sign-off.

---

## 1. Release Bundle (Ngày 1–3)

- [ ] **Package `models/release/v1.0/`:**
  ```
  models/release/v1.0/
  ├── detection/
  │   └── yolov8-plate-v1.0.pt
  ├── onnx/
  │   └── yolov8-plate-v1.onnx
  ├── configs/
  │   └── yolo_plate.yaml
  ├── MODEL_CARD.md
  ├── CONFIDENCE-SCORING.md
  ├── EVALUATION-REPORT-v1.0.md
  └── versions.json
  ```
- [ ] **Checksums:** SHA256 for each model file in `versions.json`
- [ ] **DVC tag:** `dvc push` all release artifacts
- [ ] **Verify bundle completeness:** Checklist against deliverables list

## 2. Integration Test with Backend (Ngày 3–5)

- [ ] **End-to-end 10 images via Celery worker:**
  - [ ] Start full docker stack with release models mounted
  - [ ] Upload 10 test images via API
  - [ ] Poll until terminal status
  - [ ] Verify: plate_number, confidence_score, bounding_box, needs_review populated
- [ ] **Test both inference modes:** PyTorch and ONNX feature flag
- [ ] **Test reprocess flow:** NEEDS_REVIEW → reprocess → new result
- [ ] **Test failure case:** Non-plate image → FAILED with error_message
- [ ] **Document results:** `models/release/v1.0/integration_test_results.csv`

## 3. Inference Runbook (Ngày 5–7)

- [ ] **Tạo `plan/ai-engineer/INFERENCE-RUNBOOK.md`:**
  - [ ] **Model loading:** Expected startup time, memory usage
  - [ ] **Warm-up:** First request slow — recommend warm-up task on worker start
  - [ ] **OOM troubleshooting:** Reduce concurrency, increase worker memory limit
  - [ ] **ONNX provider issues:** How to force CPU, check available providers
  - [ ] **Model update procedure:** Pull new weights → update env → restart worker
  - [ ] **Confidence tuning:** How to adjust thresholds without retraining
  - [ ] **Common errors:** Model file not found, CUDA not available, EasyOCR download fail
- [ ] **Coordinate with DevOps ONBOARDING.md:** Link runbook from there

## 4. Knowledge Transfer (Ngày 7–8)

- [ ] **Walkthrough session:** 1-hour demo of pipeline to Backend + DevOps
- [ ] **Q&A document:** Collect questions, write answers in runbook FAQ section
- [ ] **Code ownership map:** Who maintains detection vs OCR vs validation post-release

## 5. Future Roadmap (Ngày 8–9)

- [ ] **Tạo `plan/ai-engineer/ROADMAP-v1.1.md`:**
  - [ ] Multi-region plate support (VN, US, EU)
  - [ ] LPRNet / CRNN end-to-end OCR (no separate detect + OCR)
  - [ ] Active learning loop: NEEDS_REVIEW → human correction → retrain
  - [ ] Video stream LPR (frame sampling)
  - [ ] Model quantization (INT8) for edge deployment
  - [ ] PaddleOCR evaluation results (if spike done Sprint 2)
- [ ] **Priority ranking:** MoSCoW method
- [ ] **Effort estimates:** T-shirt sizes

## 6. AI Track Sign-off (Ngày 9–10)

- [ ] **Final checklist:**
  - [ ] Char accuracy ≥ 90% verified
  - [ ] MODEL_CARD complete
  - [ ] Release bundle in `models/release/v1.0/`
  - [ ] Integration test 10/10 pass
  - [ ] Runbook reviewed by Backend + DevOps
  - [ ] All sprint 0–6 AI checklists reviewed
- [ ] **Handoff email/doc:** Summary to all tracks
- [ ] **Archive notebooks:** Ensure all notebooks run with documented kernel

---

## Deliverables

| Artifact | Path |
|----------|------|
| Release bundle | `models/release/v1.0/` |
| Integration test results | `models/release/v1.0/integration_test_results.csv` |
| Inference runbook | `plan/ai-engineer/INFERENCE-RUNBOOK.md` |
| v1.1 roadmap | `plan/ai-engineer/ROADMAP-v1.1.md` |

## Sign-off

| Reviewer | Role | Date | Approved |
|----------|------|------|----------|
| | Backend Lead | | [ ] |
| | DevOps Lead | | [ ] |
| | Product Owner | | [ ] |
