# Sprint 3 — Model Artifacts (Tuần 7–8)

**Dates:** 2026-08-04 → 2026-08-17  
**Sprint Goal:** Model storage chuẩn hóa, versioning, và volume mounts cho worker inference.

---

## 1. Models Directory Structure (Ngày 1–2)

- [ ] **Finalize layout:**
  ```
  models/
  ├── detection/          # PyTorch .pt weights
  ├── onnx/               # Exported ONNX models
  ├── release/            # Versioned release bundles
  │   └── v1.0/
  ├── .gitkeep
  └── MODEL_CARD.md       # Sprint 4 AI deliverable placeholder
  ```
- [ ] **Gitignore rules:** `*.pt`, `*.onnx` in models/ (track via DVC only)
- [ ] **DVC init at repo root (if not):** `dvc init` — or keep in apps/api per current setup
- [ ] **Document decision:** Single DVC root vs per-app — pick one, document in README

## 2. DVC Workflow (Ngày 2–4)

- [ ] **Track detection model:** `dvc add models/detection/yolov8-plate-v1.pt` (job (or move from apps/api)
- [ ] **Track ONNX model:** `dvc add models/onnx/yolov8-plate-v1.onnx` when available
- [ ] **Remote config:** Verify Google Drive remote in `.dvc/config`
- [ ] **Makefile target `make models`:** `dvc pull` with error message if auth fail
- [ ] **CI/local doc:** New dev runs `make models` after clone
- [ ] **`.dvcignore`:** Exclude `datasets/raw/` large files if tracked separately

## 3. Model Versioning (Ngày 4–5)

- [ ] **Semver convention:** `{model-type}-v{major}.{minor}.pt` — e.g. `yolov8-plate-v1.0.pt`
- [ ] **Env mapping:** `PLATE_DETECTION_MODEL=models/detection/yolov8-plate-v1.0.pt`
- [ ] **Version manifest:** `models/versions.json` listing active models + checksums
- [ ] **Changelog per model:** Section in MODEL_CARD.md for each version bump
- [ ] **Rollback procedure:** Change env var → restart worker → verify

## 4. Docker Volume Mounts for Models (Ngày 5–6)

- [ ] **Mount `models/` into worker:** `./models:/app/models:ro` (read-only)
- [ ] **Mount into app (if API serves model info):** Same read-only mount
- [ ] **Env defaults point to mount paths:** `PLATE_DETECTION_MODEL=/app/models/detection/...`
- [ ] **Verify worker loads model from mount:** Not baked into image (faster rebuilds)
- [ ] **ONNX volume:** `ONNX_MODEL_PATH=/app/models/onnx/yolov8-plate-v1.onnx`

## 5. ONNX Artifact Storage (Ngày 6–7)

- [ ] **Env `USE_ONNX_INFERENCE`:** Document `true|false` default `false`
- [ ] **Storage location:** `models/onnx/` — separate from PyTorch weights
- [ ] **Export pipeline doc:** AI runs `scripts/export_onnx.py` → output to `models/onnx/`
- [ ] **Size documentation:** Record ONNX file size vs .pt for image/build planning

## 6. Model Pull in Docker Build vs Runtime (Ngày 7–8)

- [ ] **Decision doc:** Runtime pull (DVC in entrypoint) vs build-time COPY
- [ ] **Recommendation:** Runtime volume mount + `make models` on host — document rationale
- [ ] **Entrypoint script (optional):** `scripts/docker-entrypoint.sh` — wait-for-it → dvc pull → exec
- [ ] **Fallback:** If model missing, worker logs clear error, task fails gracefully

## 7. Verification (Ngày 9–10)

- [ ] **Fresh clone + pull:** New dev runs `make models` → files appear in `models/detection/`
- [ ] **Docker worker inference:** Worker loads model from volume, processes test image
- [ ] **Version switch test:** Change `PLATE_DETECTION_MODEL` → restart → new model loaded
- [ ] **Document in DevOps README:** Model setup section complete

---

## Deliverables

| Artifact | Path |
|----------|------|
| Models layout | `models/` |
| Versions manifest | `models/versions.json` |
| DVC tracked weights | `models/detection/*.pt.dvc` |
| Updated compose volumes | `docker-compose.yml` |

## Dependencies

| From | Need |
|------|------|
| AI Engineer Sprint 1 | Plate detection model file (or interim yolov8n.pt) |
| AI Engineer Sprint 4 | ONNX export for onnx/ directory |

## Stretch Goals

- [ ] **Model registry local:** Simple JSON API endpoint listing available models
- [ ] **Checksum verification:** SHA256 check on model load
