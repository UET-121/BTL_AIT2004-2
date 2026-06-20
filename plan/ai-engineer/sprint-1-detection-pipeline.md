# Sprint 1 — Detection Pipeline (Tuần 3–4)

**Dates:** 2026-07-07 → 2026-07-20  
**Sprint Goal:** Plate detection strategy decided và implemented với fallback chain, unit tests pass.

---

## 1. Detection Strategy Decision (Ngày 1)

- [ ] **Sprint Planning decision:** Chọn Option A (fine-tune) hoặc B (heuristic + client crop)
- [ ] **Document decision:** `plan/ai-engineer/DETECTION-STRATEGY.md` với rationale
- [ ] **If Option A — data requirement:** ≥ 50 labeled images ready
- [ ] **If Option B — compensating controls:** Client-side crop mandatory in Frontend Sprint 1
- [ ] **Get sign-off:** Backend + Frontend leads acknowledge impact

## 2. Fine-tune YOLO (Option A) (Ngày 1–5)

- [ ] **Tạo `configs/yolo_plate.yaml`:** Dataset paths, class names, train/val split
- [ ] **Tạo `scripts/train_yolo_plate.py`:**
  - [ ] Load base `yolov8n.pt`
  - [ ] Train on `datasets/splits/train/` labels
  - [ ] Validate on `datasets/splits/val/`
  - [ ] Output `models/detection/yolov8-plate-v1.0.pt`
- [ ] **Training params:** epochs=50, imgsz=640, batch=16 (adjust for GPU/CPU)
- [ ] **Track metrics:** mAP50, precision, recall on val set
- [ ] **DVC track output:** `dvc add models/detection/yolov8-plate-v1.0.pt`
- [ ] **Minimum acceptance:** mAP50 ≥ 0.7 on val set

## 3. Detector Interface Refactor (Ngày 3–5)

- [ ] **Review abstract [`detector.py`](../../apps/api/app/services/detection/detector.py):**
  - [ ] Interface: `detect(image: np.ndarray) -> list[BoundingBox]`
  - [ ] `BoundingBox` dataclass: x, y, width, height, confidence, class_name
- [ ] **Ensure all detectors implement interface:** YOLO, fallback, ONNX (future)
- [ ] **Factory function:** `get_detector() -> PlateDetector` reads env config
- [ ] **Singleton pattern:** Load model once at worker startup, not per request

## 4. YoloPlateDetector Implementation (Ngày 5–7)

- [ ] **Implement/refactor [`yolo_detector.py`](../../apps/api/app/services/detection/yolo_detector.py):**
  - [ ] Load model from `PLATE_DETECTION_MODEL` env path
  - [ ] Filter by `PLATE_DETECTION_CONFIDENCE` threshold (default 0.5)
  - [ ] Return best plate bbox (highest confidence) or all above threshold
  - [ ] Handle model file missing → log error, return empty list
- [ ] **Input preprocessing:** BGR numpy array from OpenCV
- [ ] **Output normalization:** Pixel coordinates relative to original image size
- [ ] **Log detection results:** confidence, bbox dimensions at DEBUG level

## 5. Fallback Chain (Ngày 7–8)

- [ ] **Implement 3-tier fallback (document in code):**
  1. [ ] **Tier 1:** Plate-specific detection (fine-tuned model or plate class)
  2. [ ] **Tier 2:** Vehicle detection (COCO car/truck/bus) → expand bbox to include plate area
  3. [ ] **Tier 3:** Full image as plate region (assume client cropped)
- [ ] **Env `USE_PLATE_DETECTION`:** `false` skips to Tier 3
- [ ] **Log which tier used:** Store in recognition metadata for analysis
- [ ] **Heuristic bbox expansion:** Vehicle box → lower 30% region for plate location

## 6. Unit Tests (Ngày 8–9)

- [ ] **Tạo `apps/api/tests/detection/test_yolo_detector.py`**
- [ ] **Fixture images:** 5 images in `apps/api/tests/fixtures/` (small JPG, git tracked)
- [ ] **Test: model loads:** Skip if model file not present (CI uses DVC pull)
- [ ] **Test: detect returns list:** Valid BoundingBox objects
- [ ] **Test: confidence filter:** Low confidence detections excluded
- [ ] **Test: fallback chain:** Mock empty detection → verify tier 2 triggered
- [ ] **Test IoU (if labeled):** bbox IoU > 0.5 with ground truth for ≥ 3/5 fixtures
- [ ] **Run:** `pytest apps/api/tests/detection/ -v`

## 7. Integration with RecognitionService (Ngày 9–10)

- [ ] **Wire detector into [`recognition.py`](../../apps/api/app/services/recognition.py):**
  - [ ] Call `detector.detect(image)` as first pipeline step
  - [ ] Crop image to bbox before OCR
  - [ ] Store `detection_confidence` and `bounding_box` in result
- [ ] **Handle no detection:** Proceed with full image + log warning
- [ ] **Manual test:** Upload 5 sample images → verify bbox stored in DB
- [ ] **Update audit metrics:** Re-run 10-image baseline, compare to Sprint 0

---

## Deliverables

| Artifact | Path |
|----------|------|
| Detection strategy doc | `plan/ai-engineer/DETECTION-STRATEGY.md` |
| Training script (Option A) | `scripts/train_yolo_plate.py` |
| YOLO config | `configs/yolo_plate.yaml` |
| Detector tests | `apps/api/tests/detection/` |
| Model weights | `models/detection/yolov8-plate-v1.0.pt` |

## Dependencies

| From | Need |
|------|------|
| Sprint 0 | Labeled dataset, audit report |
| Backend Sprint 1 | RecognitionService accepts bbox fields |
| DevOps Sprint 3 | Model volume mount path |
