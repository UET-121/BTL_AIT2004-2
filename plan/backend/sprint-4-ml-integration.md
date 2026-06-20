# Sprint 4 — ML Integration (Tuần 9–10)

**Dates:** 2026-08-18 → 2026-08-31  
**Sprint Goal:** RecognitionService wired với AI pipeline, metadata stored, integration tests pass.

---

## 1. RecognitionService Orchestrator (Ngày 1–4)

- [ ] **Port/refactor [`recognition.py`](../../apps/api/app/services/recognition.py):**
  - [ ] `recognize(image_path: str) -> RecognitionResult`
  - [ ] Pipeline steps:
    1. [ ] Load image (OpenCV)
    2. [ ] Quality assessment
    3. [ ] Plate detection (inject detector)
    4. [ ] Crop to bbox
    5. [ ] Preprocessing pipeline
    6. [ ] OCR (inject engine)
    7. [ ] Validation (inject validator)
    8. [ ] Confidence scoring
    9. [ ] Retry loop if below threshold
  - [ ] Return structured `RecognitionResult` matching AI output schema
- [ ] **Error handling:** Catch ML exceptions → return FAILED result with message

## 2. Dependency Injection (Ngày 4–5)

- [ ] **Factory functions:**
  - [ ] `get_detector()` — YOLO or ONNX based on env
  - [ ] `get_ocr_engine()` — EasyOCR singleton
  - [ ] `get_validator()` — BR validator
- [ ] **Worker startup init:** Pre-load models in `worker_process_init` signal
  - [ ] Log model load time
  - [ ] Fail fast if model file missing (configurable)
- [ ] **Lazy vs eager:** Document choice — eager recommended for predictable latency

## 3. Wire AI Deliverables (Ngày 5–6)

- [ ] **Config from env:** All ML knobs from [`config.py`](../../apps/api/app/shared/config.py)
- [ ] **Model paths:** PLATE_DETECTION_MODEL, ONNX_MODEL_PATH, USE_ONNX_INFERENCE
- [ ] **Thresholds:** NEEDS_REVIEW_THRESHOLD, AUTO_ACCEPT_THRESHOLD, MAX_PROCESSING_ATTEMPTS
- [ ] **Verify with AI release:** Use detector/OCR/validator from AI Sprint 3 deliverables
- [ ] **Sign-off AI output schema:** Matches [`05-api-contracts.md`](../_shared/05-api-contracts.md)

## 4. Store Metadata in DB (Ngày 6–7)

- [ ] **Map RecognitionResult → DB columns:**
  - [ ] plate_number ← plate_text
  - [ ] confidence_score, detection_confidence, ocr_confidence
  - [ ] needs_review ← bool
  - [ ] bounding_box ← JSON serialize BoundingBox
  - [ ] plate_region
- [ ] **Optional metadata column (stretch):** JSON field for attempts, raw_ocr, corrections
- [ ] **Status mapping in task:** COMPLETED / NEEDS_REVIEW / FAILED per confidence rules

## 5. Integration Tests (Ngày 7–9)

- [ ] **Setup testcontainers:** PostgreSQL + Redis in `conftest.py`
- [ ] **Test happy path:**
  - [ ] Upload valid plate image → poll → COMPLETED with plate_number
- [ ] **Test invalid image:**
  - [ ] Upload blank image → FAILED with error_message
- [ ] **Test review path:**
  - [ ] Upload difficult image → NEEDS_REVIEW with partial result
- [ ] **Test metadata:** confidence fields populated, bbox not null for detected plates
- [ ] **Run:** `pytest apps/api/tests/integration/ -v`

## 6. Performance Baseline (Ngày 9–10)

- [ ] **Measure single request latency:** Log processing time in task
- [ ] **Store in metadata (optional):** processing_time_ms
- [ ] **Coordinate DevOps Sprint 6:** Provide data for PERFORMANCE-BASELINE.md
- [ ] **Identify bottlenecks:** Detection vs OCR vs preprocessing — log stage timings

---

## Deliverables

| Artifact | Path |
|----------|------|
| RecognitionService | `apps/api/app/services/recognition.py` |
| Factory/DI | `apps/api/app/services/__init__.py` or dedicated factories |
| Integration tests | `apps/api/tests/integration/` |
| Worker model init | `apps/api/app/worker/celery_app.py` |

## Dependencies

| From | Need |
|------|------|
| AI Sprint 1–3 | Detector, OCR, validator, confidence formula |
| AI Sprint 4 | ONNX flag (optional this sprint) |
| Sprint 2 | Celery task to call RecognitionService |
