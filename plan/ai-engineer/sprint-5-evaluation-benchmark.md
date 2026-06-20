# Sprint 5 — Evaluation Benchmark (Tuần 11–12)

**Dates:** 2026-09-01 → 2026-09-14  
**Sprint Goal:** Frozen test set evaluation, char accuracy ≥ 90%, error analysis complete.

---

## 1. Frozen Test Set (Ngày 1–2)

- [ ] **Finalize `datasets/splits/test/`:** 100 images with ground truth labels
- [ ] **Stratified split:** Proportional Mercosul/old/edge-case representation
- [ ] **No training contamination:** Verify test images not in train/val sets
- [ ] **Manifest file:** `datasets/splits/test/manifest.csv` — filename, ground_truth, category
- [ ] **Lock test set:** Document "do not modify after this date" in README
- [ ] **DVC track (optional):** If images shared via DVC

## 2. Evaluation Script (Ngày 2–5)

- [ ] **Implement `scripts/evaluate_pipeline.py`:**
  - [ ] CLI: `--test-dir datasets/splits/test/`, `--output datasets/evaluation/results.csv`
  - [ ] For each image: run full pipeline, record predicted vs ground truth
  - [ ] Metrics computed:
    - [ ] **Char accuracy:** Character-level match / total characters
    - [ ] **Exact match rate:** Full plate string exact match
    - [ ] **Review rate:** % flagged NEEDS_REVIEW
    - [ ] **Detection IoU:** Mean IoU of bbox vs label
    - [ ] **Latency:** p50, p95 per image
    - [ ] **Failure breakdown:** By category (blur, angle, glare, format)
  - [ ] Summary printed to stdout and saved as JSON
- [ ] **Makefile target:** `make evaluate`
- [ ] **Reproducible:** Fixed random seed if any stochastic steps

## 3. Run Full Evaluation (Ngày 5–6)

- [ ] **Run on frozen test set:** Both PyTorch and ONNX modes
- [ ] **Output:** `datasets/evaluation/v1.0_results.json`
- [ ] **Verify acceptance criteria:**
  - [ ] Char accuracy ≥ 90%
  - [ ] Review rate ≤ 25%
  - [ ] Exact match rate ≥ 75%
- [ ] **If not met:** Identify gap, tune thresholds or retrain (document decision)

## 4. Error Analysis Notebook (Ngày 6–8)

- [ ] **Tạo `notebooks/02_error_analysis.ipynb`:**
  - [ ] Load evaluation results CSV
  - [ ] **Confusion patterns:** Most common OCR substitutions (O/0, I/1)
  - [ ] **Failure categorization:** Classify each error: blur, angle, glare, partial, format, other
  - [ ] **Visual gallery:** Show top 10 worst predictions with image + GT + predicted
  - [ ] **Detection failures:** Images where IoU < 0.5
  - [ ] **Review false positives:** High confidence but wrong
  - [ ] **Recommendations:** Actionable improvements for v1.1
- [ ] **Export summary:** `datasets/evaluation/error_analysis.md`

## 5. Regression Test Suite (Ngày 8–9)

- [ ] **Tạo `apps/api/tests/evaluation/test_regression.py`:**
  - [ ] Load 10 representative test images (small, git-tracked or DVC)
  - [ ] Assert char accuracy ≥ 80% on this subset (fast CI check)
  - [ ] Assert no crash on any image
  - [ ] Mark `@pytest.mark.slow` for full 100-image test
- [ ] **CI integration:** Fast subset runs in `make ci`; full eval manual pre-release

## 6. Report & Sign-off (Ngày 9–10)

- [ ] **Tạo `plan/ai-engineer/EVALUATION-REPORT-v1.0.md`:**
  - [ ] Executive summary: metrics table
  - [ ] Comparison: Sprint 0 baseline vs v1.0
  - [ ] ONNX vs PyTorch comparison
  - [ ] Known failure modes
  - [ ] Recommendations for v1.1
- [ ] **Present at Sprint Review:** Metrics dashboard
- [ ] **Sign-off:** Product owner accepts or documents waivers

---

## Deliverables

| Artifact | Path |
|----------|------|
| Evaluation script | `scripts/evaluate_pipeline.py` |
| Test set | `datasets/splits/test/` (100 images) |
| Results | `datasets/evaluation/v1.0_results.json` |
| Error analysis | `notebooks/02_error_analysis.ipynb` |
| Evaluation report | `plan/ai-engineer/EVALUATION-REPORT-v1.0.md` |

## Acceptance Gate

| Metric | Target | Actual | Pass |
|--------|--------|--------|------|
| Char accuracy | ≥ 90% | ___ | [ ] |
| Review rate | ≤ 25% | ___ | [ ] |
| Exact match | ≥ 75% | ___ | [ ] |
| p95 latency | < 30s | ___ | [ ] |
