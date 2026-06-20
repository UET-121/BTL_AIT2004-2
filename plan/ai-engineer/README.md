# AI Engineer Track — License Plate Recognition Redesign

## Scope

Nhánh AI Engineer chịu trách nhiệm toàn bộ ML pipeline: data collection, plate detection (YOLO/ONNX), preprocessing, OCR (EasyOCR), Brazilian format validation, confidence scoring, evaluation benchmark, và model handoff.

## Pipeline Overview

```
Image → Quality Assessment → Plate Detection (YOLO/ONNX)
      → Crop Region → Preprocessing (deblur/enhance/perspective)
      → EasyOCR → Brazilian Validation → Confidence Score
      → COMPLETED | NEEDS_REVIEW | FAILED
```

## Dependencies với các nhánh khác

| Nhánh | AI cần từ họ | AI cung cấp cho họ |
|-------|--------------|-------------------|
| **Backend** | Worker task interface, config env | RecognitionService output schema |
| **DevOps** | Model volume mounts, DVC setup | Model files, MODEL_CARD |
| **Frontend** | — | Confidence/bbox display data via API |

## Sprint Files

| Sprint | File | Theme |
|--------|------|-------|
| 0 | [sprint-0-data-baseline.md](sprint-0-data-baseline.md) | Dataset, labeling, audit |
| 1 | [sprint-1-detection-pipeline.md](sprint-1-detection-pipeline.md) | YOLO plate detection |
| 2 | [sprint-2-ocr-preprocessing.md](sprint-2-ocr-preprocessing.md) | EasyOCR + preprocessing |
| 3 | [sprint-3-validation-confidence.md](sprint-3-validation-confidence.md) | BR rules + scoring |
| 4 | [sprint-4-onnx-optimization.md](sprint-4-onnx-optimization.md) | ONNX export + inference |
| 5 | [sprint-5-evaluation-benchmark.md](sprint-5-evaluation-benchmark.md) | Test set eval |
| 6 | [sprint-6-model-handoff.md](sprint-6-model-handoff.md) | Release bundle |

## Key Code Paths (Current)

| Component | Path |
|-----------|------|
| Orchestrator | [`apps/api/app/services/recognition.py`](../../apps/api/app/services/recognition.py) |
| YOLO detector | [`apps/api/app/services/detection/yolo_detector.py`](../../apps/api/app/services/detection/yolo_detector.py) |
| EasyOCR | [`apps/api/app/services/ocr/easyocr_engine.py`](../../apps/api/app/services/ocr/easyocr_engine.py) |
| Preprocessing | [`apps/api/app/services/preprocessing/pipeline.py`](../../apps/api/app/services/preprocessing/pipeline.py) |
| BR validator | [`apps/api/app/services/validation/rules/brazil.py`](../../apps/api/app/services/validation/rules/brazil.py) |
| ONNX export | [`apps/api/app/models/model_packing.py`](../../apps/api/app/models/model_packing.py) |

## Acceptance Criteria (v1.0)

- Char accuracy ≥ 90% on frozen test set (100 images)
- Review rate ≤ 25%
- ONNX inference optional with < 5% accuracy drop vs PyTorch
- MODEL_CARD complete with limitations documented

## Related Docs

- [API contracts — ML output schema](../_shared/05-api-contracts.md)
- [Environment variables — ML knobs](../_shared/06-env-variables.md)
- [Risk R01, R02, R06, R08](../_shared/07-risk-register.md)
