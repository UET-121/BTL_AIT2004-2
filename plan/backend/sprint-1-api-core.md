# Sprint 1 — API Core (Tuần 3–4)

**Dates:** 2026-07-07 → 2026-07-20  
**Sprint Goal:** Recognition CRUD API hoàn chỉnh với DB model, migrations, validation, OpenAPI docs.

---

## 1. Database Model (Ngày 1–2)

- [ ] **SQLAlchemy model [`RecognitionRequest`](../../apps/api/app/models/recognition.py):**
  - [ ] `id: UUID` — primary key, default uuid4
  - [ ] `image_url: str` — path/URL to stored image
  - [ ] `plate_number: str | None` — recognized text
  - [ ] `status: RecognitionStatus` — enum
  - [ ] `error_message: str | None`
  - [ ] `created_at, updated_at: datetime` — auto timestamps
- [ ] **Status enum:** NOT_STARTED, PENDING, COMPLETED, NEEDS_REVIEW, FAILED
- [ ] **Table name:** `recognition_requests`
- [ ] **Index:** `created_at DESC` for list queries

## 2. Pydantic Schemas (Ngày 2)

- [ ] **[`schemas.py`](../../apps/api/app/models/schemas.py):**
  - [ ] `RecognitionRequestResponse` — full response with all fields
  - [ ] `RecognitionRequestSubmitResponse` — upload response
  - [ ] `RecognitionRequestListResponse` — paginated list wrapper
  - [ ] `BoundingBox` — x, y, width, height
  - [ ] `model_config = {"from_attributes": True}` for ORM conversion
- [ ] **Remove or implement empty `RecognitionRequestCreate`** (TD05 debt)

## 3. Migration 001 (Ngày 2–3)

- [ ] **Port/create migration:** [`001_create_recognition_requests.py`](../../apps/api/migrations/versions/001_create_recognition_requests.py)
- [ ] **Columns:** id, image_url, plate_number, status, error_message, created_at, updated_at
- [ ] **Run:** `make migrate` on fresh DB
- [ ] **Verify:** Table exists, enum type created

## 4. POST Upload Endpoint (Ngày 3–5)

- [ ] **`POST /api/v1/recognition`** in [`routes.py`](../../apps/api/app/api/routes.py):
  - [ ] Accept `UploadFile` via multipart form
  - [ ] Validate `content_type` starts with `image/`
  - [ ] Validate allowed types: `image/jpeg`, `image/png`
  - [ ] Max file size: 10MB (read content, check len)
  - [ ] Generate UUID filename: `{uuid}.{extension}`
  - [ ] Save via StorageService
  - [ ] INSERT with status `NOT_STARTED`
  - [ ] Return `RecognitionRequestSubmitResponse`
- [ ] **Note:** Celery queue added Sprint 2 — this sprint can sync stub or queue placeholder

## 5. GET Endpoints (Ngày 5–6)

- [ ] **`GET /api/v1/recognition/{id}`:**
  - [ ] Return full `RecognitionRequestResponse`
  - [ ] 404 if not found
- [ ] **`GET /api/v1/recognition`:**
  - [ ] Query params: `page` (≥1, default 1), `page_size` (1–100, default 10)
  - [ ] Order by `created_at DESC`
  - [ ] Return total, total_pages, items

## 6. Error Handling (Ngày 6–7)

- [ ] **Consistent error schema:** `{"detail": "message"}` or `{"detail": [...]}`
- [ ] **HTTP 400:** Invalid file type, file too large
- [ ] **HTTP 404:** Request not found
- [ ] **HTTP 422:** Pydantic validation errors (auto)
- [ ] **HTTP 500:** Unhandled — log full traceback, return generic message
- [ ] **Exception handler:** Custom handler for domain exceptions (optional)

## 7. OpenAPI Documentation (Ngày 7–8)

- [ ] **Tags:** Group under "recognition"
- [ ] **Descriptions:** Each endpoint has summary + description
- [ ] **Examples:** Request/response examples in schema
- [ ] **Verify `/docs`:** All 3 endpoints visible and try-able

## 8. API Tests (Ngày 8–10)

- [ ] **Setup pytest + httpx:** `apps/api/tests/conftest.py` with TestClient
- [ ] **Test POST upload:** Valid image → 200 + request_id
- [ ] **Test POST invalid:** PDF file → 400
- [ ] **Test GET by id:** Existing → 200, missing → 404
- [ ] **Test GET list:** Pagination math correct
- [ ] **Test DB persistence:** Upload → query DB directly → row exists

---

## Deliverables

| Artifact | Path |
|----------|------|
| Model + schemas | `apps/api/app/models/` |
| Routes | `apps/api/app/api/routes.py` |
| Migration 001 | `apps/api/migrations/versions/001_*.py` |
| Tests | `apps/api/tests/api/` |

## Dependencies

| From | Need |
|------|------|
| Sprint 0 | alembic.ini, FastAPI scaffold |
| Sprint 3 (partial) | StorageService for upload save |

## Note

StorageService basic implementation needed for upload — can implement minimal LocalStorage in this sprint if Sprint 3 not started.
