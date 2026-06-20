# Sprint 4 — ONNX Optimization (Tuần 9–10)

**Dates:** 2026-08-18 → 2026-08-31  
**Sprint Goal:** ONNX export pipeline, inference engine, benchmark shows < 5% accuracy drop, feature flag ready.

---

## 1. Export Script Standardization (Ngày 1–3)

- [ ] **Refactor [`model_packing.py`](../../apps/api/app/models/model_packing.py) → `scripts/export_onnx.py`:**
  - [ ] CLI args: `--input models/detection/yolov8-plate-v1.0.pt`, `--output models/onnx/yolov8-plate-v1.onnx`
  - [ ] Use ultralytics `model.export(format='onnx', imgsz=640, simplify=True)`
  - [ ] Verify output file size and ONNX graph validity
  - [ ] Print summary: input shape, output shape, opset version
- [ ] **Add to Makefile:** `make export-onnx`
- [ ] **DVC track ONNX:** `dvc add models/onnx/yolov8-plate-v1.onnx`
- [ ] **Document in DevOps Sprint 3:** ONNX volume mount path

## 2. ONNX Runtime Provider Probe (Ngày 2–3)

- [ ] **Reference existing [`.ipynb`](../../.ipynb):** Available providers on target machine
- [ ] **Provider priority list:**
  1. [ ] `CUDAExecutionProvider` (if GPU)
  2. [ ] `DmlExecutionProvider` (Windows DirectML)
  3. [ ] `CPUExecutionProvider` (fallback)
- [ ] **Document in `plan/ai-engineer/ONNX-SETUP.md`:** Provider selection logic
- [ ] **Env `ONNX_PROVIDER`:** Optional override, default auto-detect

## 3. OnnxPlateDetector Implementation (Ngày 3–6)

- [ ] **Tạo `apps/api/app/services/detection/onnx_detector.py`:**
  - [ ] Implements `PlateDetector` interface
  - [ ] Load model from `ONNX_MODEL_PATH` env
  - [ ] Preprocessing: resize 640×640, normalize, NCHW tensor
  - [ ] Postprocessing: NMS, confidence filter, coordinate denormalization
  - [ ] Match output format with YoloPlateDetector (same BoundingBox)
- [ ] **Factory update:** `get_detector()` checks `USE_ONNX_INFERENCE` env
  - [ ] `true` → OnnxPlateDetector
  - [ ] `false` → YoloPlateDetector (PyTorch)
- [ ] **Error handling:** Missing ONNX file → log warning, fallback to PyTorch
- [ ] **Unit test:** Mock ONNX session, verify postprocessing logic

## 4. Benchmark PT vs ONNX (Ngày 6–8)

- [ ] **Tạo `scripts/benchmark_onnx.py`:**
  - [ ] Run 100 test images through PyTorch detector
  - [ ] Run same 100 through ONNX detector
  - [ ] Metrics per run: avg latency, p95 latency, peak memory
  - [ ] Accuracy: bbox IoU match rate, detection agreement rate
  - [ ] End-to-end: full pipeline char accuracy comparison
- [ ] **Output:** `datasets/evaluation/onnx_benchmark.csv`
- [ ] **Acceptance criteria:**
  - [ ] Latency improvement ≥ 20% (or document if not achieved on CPU)
  - [ ] Accuracy drop < 5% char accuracy vs PyTorch
  - [ ] Memory usage ≤ PyTorch peak
- [ ] **If criteria not met:** Document reasons, keep feature flag default off

## 5. Feature Flag Integration (Ngày 8–9)

- [ ] **Env vars (add to `.env.example`):**
  - [ ] `USE_ONNX_INFERENCE=false`
  - [ ] `ONNX_MODEL_PATH=models/onnx/yolov8-plate-v1.onnx`
  - [ ] `ONNX_PROVIDER=` (auto)
- [ ] **Backend config:** [`config.py`](../../apps/api/app/shared/config.py) reads flags
- [ ] **Worker startup log:** Print active detector type and provider
- [ ] **Smoke test both modes:** Run smoke test with PT and ONNX flags

## 6. Model Card (Ngày 9–10)

- [ ] **Tạo `models/MODEL_CARD.md`:**
  - [ ] **Model name:** yolov8-plate-v1.0
  - [ ] **Type:** Object detection (single class: plate)
  - [ ] **Framework:** Ultralytics YOLOv8n, fine-tuned
  - [ ] **Training data:** N images, Brazil plates, date range
  - [ ] **Metrics:** mAP50, char accuracy, review rate
  - [ ] **ONNX metrics:** Latency, accuracy delta
  - [ ] **Limitations:** BR plates only, poor on heavy occlusion, night images
  - [ ] **Ethical considerations:** License plate = PII, handle with care
  - [ ] **Version history:** v1.0 release date and changes

---

## Deliverables

| Artifact | Path |
|----------|------|
| Export script | `scripts/export_onnx.py` |
| ONNX detector | `apps/api/app/services/detection/onnx_detector.py` |
| Benchmark script | `scripts/benchmark_onnx.py` |
| ONNX setup doc | `plan/ai-engineer/ONNX-SETUP.md` |
| Model card | `models/MODEL_CARD.md` |
| ONNX weights | `models/onnx/yolov8-plate-v1.onnx` |

## Verification

- [ ] `USE_ONNX_INFERENCE=true` produces same plate results as false on 10 test images
- [ ] Benchmark CSV complete with 100 images
- [ ] MODEL_CARD reviewed by Backend + DevOps leads
