# Sprint 4 — Review Workflow (Tuần 9–10)

**Dates:** 2026-08-18 → 2026-08-31  
**Sprint Goal:** NEEDS_REVIEW UX complete, reprocess for FAILED + NEEDS_REVIEW, confirmation dialogs.

---

## 1. NEEDS_REVIEW UI (Ngày 1–3)

- [ ] **Review banner on detail page:**
  - [ ] Orange alert: "This result needs manual review"
  - [ ] Show when `status === 'NEEDS_REVIEW'` or `needs_review === true`
  - [ ] Explain: confidence below threshold, result may be incorrect
- [ ] **Comparison display (if metadata available):**
  - [ ] Raw OCR text vs validated/corrected plate_number
  - [ ] Highlight differences character by character
- [ ] **List view indicator:** NEEDS_REVIEW badge already from Sprint 2 — verify prominent

## 2. Reprocess Button (Ngày 3–5)

- [ ] **Fix current gap:** Show reprocess for both FAILED and NEEDS_REVIEW (backend already supports both)
- [ ] **Button placement:** Detail page action area
- [ ] **Implement `reprocessRecognition(id)` in client.ts:**
  - [ ] POST `/api/v1/recognition/{id}/reprocess`
  - [ ] Return RecognitionSubmitResponse
- [ ] **Hide button:** When status is NOT_STARTED, PENDING, or COMPLETED
- [ ] **List view action (optional):** Reprocess icon button per row for FAILED/NEEDS_REVIEW

## 3. Confirmation Dialog (Ngày 5–6)

- [ ] **Confirm before reprocess:**
  - [ ] Modal: "Reprocess this request? Current result will be cleared."
  - [ ] Confirm / Cancel buttons
  - [ ] Focus trap in modal
- [ ] **Cancel:** Close modal, no action
- [ ] **Confirm:** Trigger reprocess mutation

## 4. Optimistic Update (Ngày 6–7)

- [ ] **On reprocess success:**
  - [ ] Immediately update local cache: status → NOT_STARTED, clear plate_number
  - [ ] Resume polling (2s interval)
  - [ ] Toast: "Reprocessing started"
- [ ] **On error:** Show error toast, revert optimistic update
- [ ] **TanStack Query:** `queryClient.setQueryData` for optimistic + `invalidateQueries` on settle

## 5. Manual Correction Form (Stretch) (Ngày 7–8)

- [ ] **Stretch goal — requires Backend endpoint `PATCH /api/v1/recognition/{id}`:**
  - [ ] Input field: editable plate_number
  - [ ] Submit button: "Confirm correction"
  - [ ] Override status to COMPLETED
- [ ] **If Backend not ready:** Document as v1.1, skip implementation
- [ ] **Dependency note:** Add to sprint integration file

## 6. Review Workflow Test (Ngày 8–10)

- [ ] **Test NEEDS_REVIEW flow:**
  1. [ ] Upload marginal quality image → NEEDS_REVIEW
  2. [ ] Banner displayed, confidence shown
  3. [ ] Click reprocess → confirm → status PENDING → new result
- [ ] **Test FAILED flow:**
  1. [ ] Upload non-plate image → FAILED
  2. [ ] Error message shown
  3. [ ] Reprocess available
- [ ] **Test COMPLETED:** No reprocess button visible
- [ ] **Demo Sprint Review:** Full review workflow

---

## Deliverables

| Artifact | Path |
|----------|------|
| Review banner | Detail page component |
| Reprocess button + dialog | Detail page + client.ts |
| Optimistic update | TanStack Query mutation |

## Dependencies

| From | Need |
|------|------|
| Backend Sprint 3 | POST reprocess endpoint |
| Backend Sprint 4 | NEEDS_REVIEW status from ML pipeline |

## Stretch

- [ ] Manual correction PATCH endpoint (Backend + Frontend coordination)
