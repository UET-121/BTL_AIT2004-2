# Sprint 2 — OCR & Preprocessing (Tuần 5–6)

**Dates:** 2026-07-21 → 2026-08-03  
**Sprint Goal:** Preprocessing pipeline chuẩn hóa, EasyOCR tuned, A/B test shows measurable improvement.

---

## 1. Preprocessing Pipeline Review (Ngày 1–3)

- [ ] **Review [`pipeline.py`](../../apps/api/app/services/preprocessing/pipeline.py):** Document current flow
- [ ] **Stage order confirmed:**
  1. [ ] Quality assessment ([`quality.py`](../../apps/api/app/services/preprocessing/quality.py))
  2. [ ] Deblur if blur score below threshold ([`deblur.py`](../../apps/api/app/services/preprocessing/deblur.py))
  3. [ ] Enhance contrast/brightness ([`enhance.py`](../../apps/api/app/services/preprocessing/enhance.py))
  4. [ ] Perspective correction if skew detected ([`perspective.py`](../../apps/api/app/services/preprocessing/perspective.py))
- [ ] **Adaptive logic:** Pipeline skips stages if quality score already high
- [ ] **Refactor if needed:** Clear `PreprocessingResult` dataclass with applied stages list
- [ ] **Unit tests per stage:** Input synthetic blurry/skewed image → verify output changed

## 2. Preprocessing Config Document (Ngày 3–4)

- [ ] **Tạo `plan/ai-engineer/preprocessing-config.md`:**
  | Stage | Trigger condition | Key parameters |
  |-------|-------------------|----------------|
  | Quality | Always | blur threshold, brightness range |
  | Deblur | blur_score < X | kernel size, Wiener params |
  | Enhance | low contrast | CLAHE clipLimit, tileGridSize |
  | Perspective | skew angle > Y° | corner detection method |
- [ ] **Map to env vars (future):** Document which params could become configurable
- [ ] **Defaults documented:** Current hardcoded values with rationale

## 3. EasyOCR Configuration (Ngày 4–5)

- [ ] **Review [`easyocr_engine.py`](../../apps/api/app/services/ocr/easyocr_engine.py):**
  - [ ] Language: `['en']` (plate characters are alphanumeric Latin)
  - [ ] Allowlist: `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`
  - [ ] `gpu=OCR_GPU` from env (default `false`)
  - [ ] Reader singleton: initialize once at worker startup
- [ ] **OCR output parsing:** Extract text, per-character confidence, bounding boxes
- [ ] **Min confidence filter:** `OCR_MIN_CONFIDENCE=0.3` — discard chars below
- [ ] **Post-OCR cleanup:** Strip spaces, dashes, dots; uppercase
- [ ] **Log raw vs cleaned text:** At DEBUG level for debugging

## 4. OCR Engine Abstraction (Ngày 5–6)

- [ ] **Verify abstract [`engine.py`](../../apps/api/app/services/ocr/engine.py):**
  - [ ] Interface: `read(image: np.ndarray) -> OCRResult`
  - [ ] `OCRResult`: text, confidence, char_confidences, raw_output
- [ ] **EasyOCR implements interface:** Swappable for future PaddleOCR/LPRNet
- [ ] **Factory:** `get_ocr_engine()` from config

## 5. Alternative OCR Spike (Optional) (Ngày 6–7)

- [ ] **Benchmark PaddleOCR vs EasyOCR:** 20 sample images
- [ ] **Notebook or script:** `notebooks/03_ocr_benchmark.ipynb`
- [ ] **Metrics:** char accuracy, latency ms, memory peak
- [ ] **Decision doc:** Keep EasyOCR or switch — document in preprocessing-config.md
- [ ] **If keep EasyOCR:** Note PaddleOCR as v1.1 consideration

## 6. Preprocessing A/B Test (Ngày 7–9)

- [ ] **Tạo `scripts/ab_test_preprocessing.py`:**
  - [ ] Run OCR on test images: raw crop vs preprocessed crop
  - [ ] Output comparison CSV: image, raw_text, enhanced_text, raw_conf, enhanced_conf
  - [ ] Summary: % images improved, % degraded, % unchanged
- [ ] **Run on ≥ 20 labeled images**
- [ ] **Acceptance:** Preprocessing improves or maintains accuracy on ≥ 70% of test set
- [ ] **Tune thresholds:** Adjust quality/blur thresholds if A/B shows regression cases
- [ ] **Document optimal config:** Update preprocessing-config.md with findings

## 7. Retry Integration (Ngày 9–10)

- [ ] **Coordinate with recognition orchestrator:**
  - [ ] Attempt 1: default preprocessing
  - [ ] Attempt 2: aggressive enhance + deblur
  - [ ] Attempt 3: perspective correction forced
- [ ] **Env `ENABLE_ENHANCED_RETRY=true`**, `MAX_PROCESSING_ATTEMPTS=3`
- [ ] **Store attempts count in metadata**
- [ ] **Test:** Blurry image triggers retry → improved result

---

## Deliverables

| Artifact | Path |
|----------|------|
| Preprocessing config | `plan/ai-engineer/preprocessing-config.md` |
| A/B test script | `scripts/ab_test_preprocessing.py` |
| OCR benchmark notebook | `notebooks/03_ocr_benchmark.ipynb` (optional) |
| Unit tests | `apps/api/tests/preprocessing/`, `apps/api/tests/ocr/` |

## Verification

- [ ] A/B test shows ≥ 70% improved or maintained
- [ ] EasyOCR singleton loads without OOM on worker start
- [ ] Retry logic produces different preprocessing on attempt 2 vs 1
