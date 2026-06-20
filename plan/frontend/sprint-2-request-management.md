# Sprint 2 — Request Management (Tuần 5–6)

**Dates:** 2026-07-21 → 2026-08-03  
**Sprint Goal:** Home page hiển thị paginated request list với status badges và auto-refresh.

---

## 1. RequestList Component (Ngày 1–3)

- [ ] **[`RequestList.tsx`](../../apps/web/src/components/RequestList.tsx):**
  - [ ] Table layout (responsive: cards on mobile in Sprint 5)
  - [ ] Columns: thumbnail, status, plate_number, created_at
  - [ ] Thumbnail: `<img>` from `/uploads/...` or image_url
  - [ ] Row click → navigate to `/requests/{id}`
  - [ ] Empty state: "No requests yet. Upload an image to get started."
- [ ] **Thumbnail fallback:** Placeholder icon if image fails to load

## 2. RequestStatus Badge (Ngày 2–3)

- [ ] **[`RequestStatus.tsx`](../../apps/web/src/components/RequestStatus.tsx):**
  - [ ] Color-coded badges:
    - [ ] `NOT_STARTED` — gray (`bg-gray-100 text-gray-700`)
    - [ ] `PENDING` — yellow (`bg-yellow-100 text-yellow-800`)
    - [ ] `COMPLETED` — green (`bg-green-100 text-green-800`)
    - [ ] `NEEDS_REVIEW` — orange (`bg-orange-100 text-orange-800`)
    - [ ] `FAILED` — red (`bg-red-100 text-red-800`)
  - [ ] Dark mode variants for each color
  - [ ] Optional: animated pulse on PENDING

## 3. List API Integration (Ngày 3–4)

- [ ] **Implement `listRecognitions(page, pageSize)` in client.ts**
- [ ] **TanStack Query `useQuery`:**
  - [ ] Query key: `['recognitions', page, pageSize]`
  - [ ] Return `RecognitionListResponse`
- [ ] **Home page [`index.tsx`](../../apps/web/src/routes/index.tsx):** Upload section + RequestList below

## 4. Pagination (Ngày 4–5)

- [ ] **Prev/Next buttons:** Disable at first/last page
- [ ] **Page indicator:** "Page X of Y"
- [ ] **Page size selector:** 10, 25, 50 (default 10)
- [ ] **Total count display:** "Showing X of Y requests"
- [ ] **URL state (optional):** Sync page to query param `?page=2`

## 5. Auto-Refresh (Ngày 5–6)

- [ ] **Conditional polling:** `refetchInterval: 5000` when any item has status NOT_STARTED or PENDING
- [ ] **Stop polling:** When all items terminal (COMPLETED, NEEDS_REVIEW, FAILED)
- [ ] **Manual refresh button:** Icon button to force refetch
- [ ] **Stale indicator:** Subtle "Updating..." text during refetch

## 6. Types Update (Ngày 6)

- [ ] **Ensure `RecognitionStatus` includes NEEDS_REVIEW** in [`types/index.ts`](../../apps/web/src/types/index.ts)
- [ ] **Add optional confidence fields** to RecognitionRequest type (prep Sprint 3)

## 7. Verification (Ngày 7–10)

- [ ] **Upload 3 images:** All appear in list
- [ ] **Status updates:** PENDING → COMPLETED visible without manual refresh
- [ ] **Pagination:** With 15+ requests, page navigation works
- [ ] **Empty state:** Fresh DB shows CTA
- [ ] **Dark mode:** Badges readable in both themes
- [ ] **Demo:** List auto-updates during Sprint Review

---

## Deliverables

| Artifact | Path |
|----------|------|
| RequestList | `apps/web/src/components/RequestList.tsx` |
| RequestStatus | `apps/web/src/components/RequestStatus.tsx` |
| List API | `apps/web/src/api/client.ts` |
| Updated home | `apps/web/src/routes/index.tsx` |
| Updated types | `apps/web/src/types/index.ts` |

## Dependencies

| From | Need |
|------|------|
| Backend Sprint 1 | GET list endpoint |
| Backend Sprint 2 | Async status changes to demonstrate polling |
