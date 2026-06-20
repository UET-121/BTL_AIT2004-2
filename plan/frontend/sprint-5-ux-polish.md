# Sprint 5 — UX Polish (Tuần 11–12)

**Dates:** 2026-09-01 → 2026-09-14  
**Sprint Goal:** Responsive mobile layout, accessibility pass, skeleton loaders, 404 page.

---

## 1. Responsive Layout (Ngày 1–3)

- [ ] **Home page mobile:**
  - [ ] Upload zone full width on ≤768px
  - [ ] RequestList: table → card layout on mobile
  - [ ] Card shows: thumbnail, status badge, plate, date, tap → detail
- [ ] **Detail page mobile:**
  - [ ] Single column stack: image on top, info below
  - [ ] Confidence bars full width
  - [ ] Action buttons full width stacked
- [ ] **Header:** Hamburger menu unnecessary (minimal nav) — ensure title fits
- [ ] **Test viewports:** 375px (iPhone SE), 768px (iPad), 1280px (desktop)

## 2. Accessibility (Ngày 3–5)

- [ ] **ARIA labels:**
  - [ ] Upload drop zone: `aria-label="Upload license plate image"`
  - [ ] Status badges: `aria-label="Status: Completed"`
  - [ ] Confidence bars: `role="progressbar"` with aria-valuenow
  - [ ] Reprocess button: descriptive label
- [ ] **Keyboard navigation:**
  - [ ] Tab order logical on all pages
  - [ ] Enter/Space activates buttons
  - [ ] Escape closes cropper modal and confirm dialog
- [ ] **Focus trap:** Cropper modal and confirm dialog (verify)
- [ ] **Color contrast:** WCAG AA for text and badges in both themes
- [ ] **Screen reader test:** VoiceOver or NVDA walkthrough

## 3. Skeleton Loaders (Ngày 5–6)

- [ ] **List skeleton:** 5 row placeholders while loading
- [ ] **Detail skeleton:** Image rectangle + text lines placeholder
- [ ] **Tailwind animate-pulse** styling
- [ ] **Replace spinners** where skeleton provides better UX

## 4. 404 Page (Ngày 6–7)

- [ ] **Unknown route 404:** TanStack Router notFoundComponent
- [ ] **Unknown request ID:** Detail page shows "Request not found" with link home
- [ ] **Styling:** Consistent with app theme, helpful message

## 5. i18n Prep (Optional) (Ngày 7–8)

- [ ] **Externalize strings:** Create `src/i18n/strings.ts` or JSON
  - [ ] English default
  - [ ] PT-BR translations for key UI strings (Brazilian product)
- [ ] **No full i18n library required** — just string extraction for future
- [ ] **If deferred:** Document strings to translate in v1.1

## 6. Visual Polish (Ngày 8–9)

- [ ] **Consistent spacing:** Review padding/margins across pages
- [ ] **Typography hierarchy:** h1/h2/body consistent
- [ ] **Hover states:** Buttons, table rows, cards
- [ ] **Transition animations:** Subtle fade-in for loaded content
- [ ] **Favicon:** Add plate-themed favicon (optional)

## 7. Verification (Ngày 9–10)

- [ ] **Mobile test:** Full flow on 375px viewport
- [ ] **a11y audit:** Lighthouse accessibility score ≥ 90
- [ ] **Dark mode:** All polish items work in dark theme
- [ ] **Skeleton → content:** No layout shift on load

---

## Deliverables

| Artifact | Path |
|----------|------|
| Responsive styles | Components + routes |
| Skeleton components | `apps/web/src/components/Skeleton*.tsx` |
| 404 page | Route notFoundComponent |
| i18n strings (optional) | `apps/web/src/i18n/` |

## Verification

- [ ] Lighthouse accessibility ≥ 90
- [ ] Mobile upload → detail flow works
- [ ] Keyboard-only navigation possible
