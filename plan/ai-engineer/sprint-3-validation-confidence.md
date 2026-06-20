# Sprint 3 — Validation & Confidence (Tuần 7–8)

**Dates:** 2026-08-04 → 2026-08-17  
**Sprint Goal:** Brazilian validation rules complete, confidence formula tuned, output schema delivered to Backend.

---

## 1. Brazilian Validator Review (Ngày 1–3)

- [ ] **Review [`brazil.py`](../../apps/api/app/services/validation/rules/brazil.py):**
  - [ ] **Mercosul format:** `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$` — e.g. `ABC1D23`
  - [ ] **Old format:** `^[A-Z]{3}[0-9]{4}$` — e.g. `ABC1234`
  - [ ] **Case insensitive input:** Normalize to uppercase before validation
- [ ] **OCR error corrections:**
  - [ ] `O→0`, `I→1`, `Z→2`, `S→5`, `B→8` (context-aware position rules)
  - [ ] Position-aware: letters only in alpha positions, digits in digit positions
- [ ] **Unit tests:** 20+ test cases covering valid, invalid, correctable OCR errors
- [ ] **Edge cases:** Partial reads, extra characters, missing characters

## 2. Validator Interface (Ngày 3–4)

- [ ] **Review [`validator.py`](../../apps/api/app/services/validation/validator.py):**
  - [ ] `validate(text, region='BR') -> ValidationResult`
  - [ ] `ValidationResult`: is_valid, corrected_text, corrections_applied, validation_score
- [ ] **Region factory:** `DEFAULT_PLATE_REGION=BR` from env
- [ ] **Extensibility:** Base rule class in [`base.py`](../../apps/api/app/services/validation/rules/base.py) for future regions

## 3. Confidence Scoring Formula (Ngày 4–6)

- [ ] **Tạo `plan/ai-engineer/CONFIDENCE-SCORING.md`:**
  ```
  confidence_score = w1 * detection_confidence
                   + w2 * ocr_confidence
                   + w3 * validation_score
  
  Default weights: w1=0.2, w2=0.5, w3=0.3
  ```
- [ ] **validation_score:** 1.0 if exact match, 0.8 if corrected, 0.0 if invalid
- [ ] **needs_review flag:** `confidence_score < NEEDS_REVIEW_THRESHOLD` (0.6)
- [ ] **auto accept:** `confidence_score >= AUTO_ACCEPT_THRESHOLD` (0.85)
- [ ] **Implement in recognition orchestrator:** Compute after validation step
- [ ] **Store all components separately in DB:** detection, ocr, combined

## 4. Threshold Tuning (Ngày 6–8)

- [ ] **Grid search script:** `scripts/tune_thresholds.py`
  - [ ] Vary NEEDS_REVIEW_THRESHOLD: 0.4, 0.5, 0.6, 0.7
  - [ ] Vary AUTO_ACCEPT_THRESHOLD: 0.75, 0.80, 0.85, 0.90
  - [ ] Measure: char_accuracy, review_rate, false_accept_rate on val set
- [ ] **Target:** review_rate ≤ 25%, char_accuracy ≥ 90%
- [ ] **Update env defaults:** Based on grid search results
- [ ] **Document chosen thresholds** in CONFIDENCE-SCORING.md with justification

## 5. Retry Strategy Finalization (Ngày 8–9)

- [ ] **Review retry in [`recognition.py`](../../apps/api/app/services/recognition.py):**
  - [ ] Retry if validation fails OR confidence below threshold
  - [ ] Max attempts: `MAX_PROCESSING_ATTEMPTS=3`
  - [ ] Different preprocessing per attempt (Sprint 2 integration)
  - [ ] Best attempt wins (highest confidence)
- [ ] **Final status mapping:**
  - [ ] Valid + high confidence → `COMPLETED`
  - [ ] Valid + low confidence → `NEEDS_REVIEW`
  - [ ] Invalid after all retries → `FAILED`
- [ ] **Error message:** Meaningful message in `error_message` field for FAILED

## 6. Output Schema for Backend (Ngày 9–10)

- [ ] **Deliver JSON spec** (also in [`05-api-contracts.md`](../_shared/05-api-contracts.md)):
  ```json
  {
    "plate_text": "ABC1D23",
    "confidence_score": 0.92,
    "detection_confidence": 0.88,
    "ocr_confidence": 0.95,
    "needs_review": false,
    "bounding_box": {"x": 120, "y": 200, "width": 180, "height": 60},
    "plate_region": "BR",
    "metadata": {
      "attempts": 1,
      "preprocessing_applied": ["enhance"],
      "raw_ocr_text": "ABC1D23",
      "validation_corrections": [],
      "detection_tier": 1
    }
  }
  ```
- [ ] **Backend sign-off:** Backend lead confirms schema matches DB columns
- [ ] **Integration test:** 5 images through full pipeline → verify all fields populated

---

## Deliverables

| Artifact | Path |
|----------|------|
| Confidence scoring doc | `plan/ai-engineer/CONFIDENCE-SCORING.md` |
| Threshold tuning script | `scripts/tune_thresholds.py` |
| Validator unit tests | `apps/api/tests/validation/test_brazil.py` |
| Output schema | `_shared/05-api-contracts.md` (updated) |

## Verification

- [ ] 20+ validator unit tests pass
- [ ] Grid search results documented
- [ ] Backend stores all confidence fields correctly
