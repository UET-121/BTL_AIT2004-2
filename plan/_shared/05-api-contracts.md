# API Contracts — Draft Specification

Đồng bộ với code hiện tại tại [`apps/api/app/api/routes.py`](../../apps/api/app/api/routes.py) và [`schemas.py`](../../apps/api/app/models/schemas.py). Mọi thay đổi API phải cập nhật file này trước khi implement.

**Base URL (dev):** `http://localhost:8000`  
**Base URL (docker web proxy):** `http://localhost/api`  
**OpenAPI:** `GET /docs`, `GET /openapi.json`

---

## Health

### `GET /health`

**Response 200:**

```json
{
  "status": "ok"
}
```

**Extended (Sprint 2+):**

```json
{
  "status": "ok",
  "db": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

---

## Recognition

Prefix: `/api/v1/recognition`

### Status Enum

| Value | Description |
|-------|-------------|
| `NOT_STARTED` | Request created, task not yet picked up |
| `PENDING` | Worker processing |
| `COMPLETED` | Plate recognized, confidence acceptable |
| `NEEDS_REVIEW` | Result exists but confidence below threshold |
| `FAILED` | Processing failed after retries |

### `POST /api/v1/recognition`

Upload license plate image for async recognition.

**Request:** `multipart/form-data`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `file` | File | Yes | `image/jpeg`, `image/png`; max 10MB |

**Response 200:** `RecognitionRequestSubmitResponse`

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "NOT_STARTED",
  "created_at": "2026-06-23T10:00:00Z"
}
```

**Errors:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Not an image | `{"detail": "File must be an image"}` |
| 413 | File too large (Sprint 5+) | `{"detail": "File exceeds 10MB limit"}` |
| 422 | Validation error | FastAPI default |
| 429 | Rate limited (Sprint 5+) | `{"detail": "Too many requests"}` |

**Side effects:**

1. Save file to storage → `image_url`
2. INSERT `recognition_requests` with `status=NOT_STARTED`
3. Enqueue Celery task `process_plate_recognition`

---

### `GET /api/v1/recognition/{request_id}`

**Path params:** `request_id` (UUID)

**Response 200:** `RecognitionRequestResponse`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "image_url": "/uploads/550e8400-e29b-41d4-a716-446655440000.jpg",
  "plate_number": "ABC1D23",
  "status": "COMPLETED",
  "error_message": null,
  "created_at": "2026-06-23T10:00:00Z",
  "updated_at": "2026-06-23T10:00:05Z",
  "confidence_score": 0.92,
  "detection_confidence": 0.88,
  "ocr_confidence": 0.95,
  "needs_review": false,
  "bounding_box": {
    "x": 120,
    "y": 200,
    "width": 180,
    "height": 60
  },
  "plate_region": "BR"
}
```

**Errors:**

| Status | Condition |
|--------|-----------|
| 404 | Request not found |

---

### `GET /api/v1/recognition`

Paginated list of recognition requests.

**Query params:**

| Param | Type | Default | Constraints |
|-------|------|---------|-------------|
| `page` | int | 1 | ≥ 1 |
| `page_size` | int | 10 | 1–100 |

**Response 200:** `RecognitionRequestListResponse`

```json
{
  "items": [ /* RecognitionRequestResponse[] */ ],
  "total": 42,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

---

### `POST /api/v1/recognition/{request_id}/reprocess`

Re-queue a failed or needs-review request.

**Path params:** `request_id` (UUID)

**Response 200:** `RecognitionRequestSubmitResponse`

**Errors:**

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Not found | `{"detail": "Recognition request not found"}` |
| 400 | Invalid status | `{"detail": "Only FAILED or NEEDS_REVIEW requests can be reprocessed"}` |

**Side effects:**

1. Reset result fields (plate_number, confidence, bbox, etc.)
2. SET `status=NOT_STARTED`
3. Enqueue Celery task

---

## Static Files

### `GET /uploads/{filename}`

Serve uploaded images from local storage.

**Response:** Image binary (JPEG/PNG)

---

## Celery Task Contract (Internal)

### Task: `process_plate_recognition`

**Input:** `request_id: str` (UUID string)

**Output schema (stored in DB by worker):**

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
    "preprocessing_applied": ["enhance", "perspective"],
    "raw_ocr_text": "ABC1D23",
    "validation_corrections": []
  }
}
```

**Status mapping:**

| Condition | Final status |
|-----------|--------------|
| `confidence_score >= AUTO_ACCEPT_THRESHOLD` | `COMPLETED` |
| `confidence_score < NEEDS_REVIEW_THRESHOLD` | `NEEDS_REVIEW` |
| Exception / no valid plate after max retries | `FAILED` |

---

## Frontend TypeScript Mirror

Target types in `apps/web/src/types/index.ts`:

```typescript
export type RecognitionStatus =
  | "NOT_STARTED"
  | "PENDING"
  | "COMPLETED"
  | "NEEDS_REVIEW"
  | "FAILED";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface RecognitionRequest {
  id: string;
  image_url: string;
  plate_number: string | null;
  status: RecognitionStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  confidence_score?: number | null;
  detection_confidence?: number | null;
  ocr_confidence?: number | null;
  needs_review?: boolean;
  bounding_box?: BoundingBox | null;
  plate_region?: string | null;
}
```

---

## Future Endpoints (Stretch — Sprint 4+)

### `PATCH /api/v1/recognition/{request_id}` (Manual correction)

**Request:**

```json
{
  "plate_number": "ABC1D23",
  "override_status": "COMPLETED"
}
```

**Dependency:** Backend Sprint 4 + Frontend Sprint 4 stretch goal.

---

## Versioning

- Current: `v1` (URL prefix `/api/v1/`)
- Header (Sprint 5+): `X-API-Version: v1`
- Breaking changes → new prefix `/api/v2/`
