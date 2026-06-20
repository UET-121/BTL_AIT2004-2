# Sprint 1 — Upload Flow (Tuần 3–4)

**Dates:** 2026-07-07 → 2026-07-20  
**Sprint Goal:** User có thể upload ảnh biển số (drag-drop + crop) và redirect tới detail page.

---

## 1. ImageUpload Component (Ngày 1–3)

- [ ] **[`ImageUpload.tsx`](../../apps/web/src/components/ImageUpload.tsx):**
  - [ ] Drag-and-drop zone với visual feedback (border highlight on dragover)
  - [ ] Click to browse file input (hidden)
  - [ ] Accept: `image/jpeg`, `image/png`
  - [ ] Client-side max size: 10MB — show error before upload
  - [ ] Preview selected image before crop/upload
  - [ ] Disabled state during upload
- [ ] **Styling:** Tailwind, dark mode compatible
- [ ] **Accessibility:** Keyboard accessible file input, aria-label on drop zone

## 2. ImageCropper Modal (Ngày 3–5)

- [ ] **[`ImageCropper.tsx`](../../apps/web/src/components/ImageCropper.tsx):**
  - [ ] Modal overlay with crop area
  - [ ] `react-easy-crop` integration
  - [ ] Aspect ratio: 3:1 (plate-like) — configurable prop
  - [ ] Zoom slider
  - [ ] Confirm / Cancel buttons
  - [ ] Output cropped image as Blob for upload
- [ ] **Canvas crop utility:** Convert crop area to JPEG blob
- [ ] **Flow:** Select image → cropper modal → confirm → upload

## 3. Upload Mutation (Ngày 5–6)

- [ ] **Implement `uploadRecognition(file: File)` in client.ts:**
  - [ ] POST multipart/form-data to `/api/v1/recognition`
  - [ ] Field name: `file`
  - [ ] Return `RecognitionSubmitResponse`
- [ ] **TanStack Query `useMutation`:**
  - [ ] `mutationFn`: uploadRecognition
  - [ ] `onSuccess`: navigate to `/requests/{request_id}`
  - [ ] `onError`: show error message
- [ ] **Invalidate list query** on success (prep Sprint 2)

## 4. Success & Error Flows (Ngày 6–7)

- [ ] **Success:** Redirect to `/requests/{requestId}` using TanStack Router navigate
- [ ] **Error toast/alert:**
  - [ ] Network error: "Unable to connect to server"
  - [ ] 400: Show server detail message
  - [ ] 413: "File too large (max 10MB)"
  - [ ] Generic 500: "Upload failed, please try again"
- [ ] **Loading spinner:** Overlay or button disabled during upload

## 5. Home Page Integration (Ngày 7–8)

- [ ] **[`index.tsx`](../../apps/web/src/routes/index.tsx):**
  - [ ] Upload section at top with ImageUpload component
  - [ ] Heading: "Upload License Plate Image"
  - [ ] Instructions text: supported formats, max size
- [ ] **Placeholder for list:** Empty div or "Coming Sprint 2" → replace Sprint 2

## 6. Detail Page Stub (Ngày 8–9)

- [ ] **[`$requestId.tsx`](../../apps/web/src/routes/requests/$requestId.tsx):**
  - [ ] Read `requestId` from route params
  - [ ] Fetch request via `getRecognition(requestId)`
  - [ ] Display: id, status, created_at (minimal — full Sprint 3)
- [ ] **Loading state:** Skeleton or spinner while fetching
- [ ] **404 state:** Request not found message

## 7. Verification (Ngày 9–10)

- [ ] **Manual test:** Upload JPEG → crop → redirect to detail
- [ ] **Upload PNG without crop:** Skip crop option or force crop — document behavior
- [ ] **Upload > 10MB:** Client rejects before API call
- [ ] **Upload non-image:** Client rejects
- [ ] **Backend receives cropped image:** Verify smaller than original if cropped
- [ ] **Demo Sprint Review:** Live upload demo

---

## Deliverables

| Artifact | Path |
|----------|------|
| ImageUpload | `apps/web/src/components/ImageUpload.tsx` |
| ImageCropper | `apps/web/src/components/ImageCropper.tsx` |
| Upload API | `apps/web/src/api/client.ts` |
| Home route | `apps/web/src/routes/index.tsx` |
| Detail stub | `apps/web/src/routes/requests/$requestId.tsx` |

## Dependencies

| From | Need |
|------|------|
| Backend Sprint 1 | POST /api/v1/recognition |
| Backend Sprint 2 | Async processing for meaningful detail page |

## AI Coordination

Client-side crop compensates for generic YOLO detection (R01) — crop before upload improves OCR accuracy.
