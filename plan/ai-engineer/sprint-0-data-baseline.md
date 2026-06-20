# Sprint 0 — Data Baseline (Tuần 1–2)

**Dates:** 2026-06-23 → 2026-07-06  
**Sprint Goal:** Dataset structure, labeling guidelines, baseline metrics template, và audit model hiện tại.

---

## 1. Dataset Directory Structure (Ngày 1–2)

- [ ] **Tạo `datasets/README.md`:** Mô tả cấu trúc và quy tắc sử dụng
- [ ] **Tạo thư mục:**
  ```
  datasets/
  ├── raw/                  # Original images (gitignored)
  │   └── br_plates/
  ├── processed/            # Cropped/enhanced versions
  ├── splits/
  │   ├── train/
  │   ├── val/
  │   └── test/
  ├── labels/               # YOLO format labels
  └── evaluation/           # Metrics outputs
  ```
- [ ] **Gitignore:** `datasets/raw/**`, `datasets/processed/**` — không commit ảnh lớn
- [ ] **DVC tracking (optional):** `dvc add datasets/raw/br_plates` nếu cần share team

## 2. Sample Image Collection (Ngày 2–4)

- [ ] **Thu thập tối thiểu 50 ảnh biển số Brazil:** Đặt trong `datasets/raw/br_plates/`
- [ ] **Mercosul format (ABC1D23):** ≥ 25 ảnh — chữ + số xen kẽ
- [ ] **Old format (ABC1234):** ≥ 15 ảnh — 3 chữ + 4 số
- [ ] **Edge cases:** ≥ 10 ảnh — blur, góc nghiêng, glare, tối, bẩn
- [ ] **Metadata CSV:** `datasets/raw/manifest.csv` — columns: filename, format, source, notes
- [ ] **License check:** Document nguồn ảnh, đảm bảo không vi phạm bản quyền

## 3. Labeling Guidelines (Ngày 4–5)

- [ ] **Tạo `datasets/LABELING.md`:**
  - [ ] **Detection labels:** YOLO format `class x_center y_center width height` (normalized 0–1)
  - [ ] **Class 0:** `plate` — bounding box bao quanh toàn bộ biển số
  - [ ] **OCR ground truth:** File `.txt` cùng tên ảnh, nội dung plate text uppercase
  - [ ] **Quality guidelines:** Box sát mép biển, không include bumper quá nhiều
  - [ ] **Tool recommendation:** LabelImg, CVAT, hoặc Roboflow
- [ ] **Label 10 ảnh pilot:** Verify inter-annotator agreement nếu 2 người label

## 4. Baseline Metrics Template (Ngày 5–6)

- [ ] **Tạo `datasets/evaluation/metrics_template.csv`:**
  ```
  image,ground_truth,predicted,confidence,latency_ms,detection_iou,status,error_type
  ```
- [ ] **Tạo `datasets/evaluation/README.md`:** Giải thích từng column
- [ ] **Script stub:** `scripts/evaluate_pipeline.py` — print "not implemented" (implement Sprint 5)
- [ ] **Baseline run on current system:** Chạy 10 ảnh qua pipeline hiện tại, ghi kết quả vào CSV

## 5. Audit Model Hiện Tại (Ngày 6–7)

- [ ] **Review [`yolo_detector.py`](../../apps/api/app/services/detection/yolo_detector.py):**
  - [ ] Document: dùng `yolov8n.pt` — COCO pretrained, 80 classes
  - [ ] Không có class "license_plate" trong COCO
  - [ ] Fallback: vehicle detection (class car/truck/bus) → crop
  - [ ] Fallback 2: full image nếu không detect được
- [ ] **Viết audit report:** `plan/ai-engineer/AUDIT-current-model.md`
- [ ] **Measure baseline detection rate:** % ảnh có bbox IoU > 0.5 với manual labels (10 pilot images)
- [ ] **Identify top failure modes:** List 3–5 patterns (angle, distance, occlusion)

## 6. Exploration Notebook (Ngày 7–9)

- [ ] **Tạo `notebooks/01_data_exploration.ipynb`:**
  - [ ] Load sample images từ `datasets/raw/br_plates/`
  - [ ] Histogram: image width × height distribution
  - [ ] Histogram: aspect ratio (plate ~ 3:1)
  - [ ] Blur score distribution (Laplacian variance từ quality module)
  - [ ] Sample visualizations: 2×5 grid random images
  - [ ] Format distribution pie chart: Mercosul vs old
- [ ] **Notebook chạy top-to-bottom không lỗi**
- [ ] **Export key stats:** Ghi vào audit report

## 7. Detection Strategy Decision Prep (Ngày 9–10)

- [ ] **Document options for Sprint 1:**
  - [ ] **Option A:** Fine-tune YOLOv8n on plate dataset (50+ labeled images)
  - [ ] **Option B:** Heuristic + client-side crop only (MVP, no fine-tune)
  - [ ] **Option C:** Use pre-trained LPR model from open source (research)
- [ ] **Trade-off matrix:** Accuracy vs effort vs timeline
- [ ] **Recommendation draft:** Present in Sprint 1 planning
- [ ] **ONNX probe notebook (existing):** Reference [`.ipynb`](../../.ipynb) — available providers on dev machine

---

## Deliverables

| Artifact | Path |
|----------|------|
| Dataset structure | `datasets/` |
| Labeling guide | `datasets/LABELING.md` |
| Metrics template | `datasets/evaluation/metrics_template.csv` |
| Model audit | `plan/ai-engineer/AUDIT-current-model.md` |
| Exploration notebook | `notebooks/01_data_exploration.ipynb` |

## Dependencies

| From | Need |
|------|------|
| DevOps Sprint 0 | `models/` directory, DVC docs |
| Backend Sprint 0 | Pipeline runnable for baseline metrics |
