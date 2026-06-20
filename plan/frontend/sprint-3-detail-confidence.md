# Sprint 3 — Detail & Confidence (Tuần 7–8)

**Dates:** 2026-08-04 → 2026-08-17  
**Sprint Goal:** Detail page hiển thị confidence scores, bounding box overlay, metadata panel.

---

## 1. Detail Page Layout (Ngày 1–2)

- [ ] **Expand [`$requestId.tsx`](../../apps/web/src/routes/requests/$requestId.tsx):**
  - [ ] Two-column layout: image left, info right (stack on mobile)
  - [ ] Back link to home
  - [ ] Request ID (truncated UUID), created_at, updated_at
  - [ ] Status badge (reuse RequestStatus)
  - [ ] Plate number prominently displayed when available

## 2. Polling (Ngày 2–3)

- [ ] **TanStack Query polling:**
  - [ ] `refetchInterval: 2000` when status is NOT_STARTED or PENDING
  - [ ] Stop polling on terminal status
- [ ] **Processing indicator:** Spinner + "Processing..." text during PENDING
- [ ] **Transition animation:** Status change highlight (subtle flash)

## 3. Confidence Display (Ngày 3–5)

- [ ] **Confidence section:**
  - [ ] **Overall score:** Progress bar 0–100% with color (green ≥85, orange ≥60, red <60)
  - [ ] **Breakdown:**
    - [ ] Detection confidence: `detection_confidence`
    - [ ] OCR confidence: `ocr_confidence`
    - [ ] Combined: `confidence_score`
  - [ ] **Needs review flag:** Warning badge if `needs_review === true`
- [ ] **Hide section:** When all confidence fields null (still processing)
- [ ] **Tooltip/info:** Explain what each score means

## 4. Bounding Box Overlay (Ngày 5–7)

- [ ] **ImageWithBbox component:**
  - [ ] Display uploaded image full width in container
  - [ ] SVG or canvas overlay drawing rectangle from `bounding_box`
  - [ ] Coordinates: x, y, width, height (pixel values from API)
  - [ ] Box style: semi-transparent green border, label "Plate"
  - [ ] Handle missing bbox: show image without overlay
- [ ] **Responsive scaling:** Bbox scales correctly when image resized in container
- [ ] **Test with known bbox:** Verify alignment on sample image

## 5. Metadata Panel (Ngày 7–8)

- [ ] **Info panel:**
  - [ ] Plate region: `plate_region` (e.g., "BR")
  - [ ] Processing time: `updated_at - created_at` computed
  - [ ] Error message: displayed if FAILED (red alert box)
  - [ ] Image URL link: open full image in new tab
- [ ] **Future metadata (optional):** attempts count if API provides

## 6. Image Viewer (Ngày 8–9)

- [ ] **Zoom controls:** +/- buttons or scroll wheel zoom
- [ ] **Fit to container:** Default scale to fit
- [ ] **Reset zoom button**
- [ ] **Works with bbox overlay:** Zoom scales both image and overlay together

## 7. Verification (Ngày 9–10)

- [ ] **Upload → detail:** Poll shows status transition live
- [ ] **COMPLETED request:** Plate number + confidence visible
- [ ] **NEEDS_REVIEW request:** Orange warning + confidence < threshold
- [ ] **FAILED request:** Error message displayed, no confidence
- [ ] **Bbox overlay:** Visible on detected plates, absent on failures
- [ ] **Dark mode:** All new components styled correctly

---

## Deliverables

| Artifact | Path |
|----------|------|
| Detail page | `apps/web/src/routes/requests/$requestId.tsx` |
| ImageWithBbox | `apps/web/src/components/ImageWithBbox.tsx` |
| Confidence UI | `apps/web/src/components/ConfidenceDisplay.tsx` |

## Dependencies

| From | Need |
|------|------|
| Backend Sprint 4 | Confidence + bbox fields populated |
| AI Sprint 3 | Confidence scoring active |
