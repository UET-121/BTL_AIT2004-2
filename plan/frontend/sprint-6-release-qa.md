# Sprint 6 — Release QA (Tuần 13–14)

**Dates:** 2026-09-15 → 2026-09-28  
**Sprint Goal:** Playwright E2E tests, production build verified, Lighthouse ≥ 85, browser matrix tested.

---

## 1. Playwright Setup (Ngày 1–2)

- [ ] **Install Playwright:** `pnpm add -D @playwright/test`
- [ ] **Config `playwright.config.ts`:**
  - [ ] Base URL: `http://localhost` (nginx docker) or `http://localhost:5173` (dev)
  - [ ] Screenshot on failure
  - [ ] Retry: 1
  - [ ] Projects: chromium, firefox, webkit (or chromium only for CI speed)
- [ ] **Fixture image:** `apps/web/e2e/fixtures/plate-sample.jpg` (small, git tracked)
- [ ] **Script:** `"test:e2e": "playwright test"` in package.json

## 2. E2E Test Scenarios (Ngày 2–5)

- [ ] **`e2e/upload-flow.spec.ts`:**
  - [ ] Navigate to home
  - [ ] Upload fixture image
  - [ ] (Skip crop or confirm crop modal)
  - [ ] Redirected to detail page
  - [ ] Wait for terminal status (timeout 60s)
  - [ ] Assert plate_number visible or FAILED with message
- [ ] **`e2e/list-flow.spec.ts`:**
  - [ ] Home shows request list
  - [ ] Click row → navigates to detail
  - [ ] Back navigation works
- [ ] **`e2e/reprocess-flow.spec.ts`:**
  - [ ] Find or create FAILED request
  - [ ] Click reprocess → confirm dialog → status changes to PENDING
  - [ ] Wait for new terminal status
- [ ] **`e2e/theme-toggle.spec.ts`:**
  - [ ] Toggle dark mode → `<html>` has `dark` class
  - [ ] Reload → theme persisted

## 3. Production Build Verify (Ngày 5–6)

- [ ] **`pnpm build`:** Zero errors, zero warnings (or documented accepts)
- [ ] **Docker web build:** `docker compose build web` succeeds
- [ ] **Serve via nginx:** `http://localhost` (port 80)
- [ ] **Verify proxy:** API calls work through nginx `/api`
- [ ] **Verify uploads serve:** Images load through `/uploads`
- [ ] **SPA routing:** Direct URL `/requests/{id}` returns index.html, client routes correctly

## 4. Performance (Ngày 6–7)

- [ ] **Lighthouse audit on production build:**
  - [ ] Performance ≥ 85
  - [ ] Accessibility ≥ 90 (from Sprint 5)
  - [ ] Best practices ≥ 90
  - [ ] SEO ≥ 80 (minimal SPA)
- [ ] **Bundle size check:** Main chunk < 500KB gzipped
- [ ] **Document results:** `plan/frontend/LIGHTHOUSE-REPORT.md`

## 5. Browser Matrix (Ngày 7–8)

- [ ] **Test matrix document `plan/frontend/BROWSER-MATRIX.md`:**
  | Browser | Version | Upload | List | Detail | Reprocess | Pass |
  |---------|---------|--------|------|--------|-----------|------|
  | Chrome | latest | | | | | [ ] |
  | Firefox | latest | | | | | [ ] |
  | Edge | latest | | | | | [ ] |
  | Safari | latest (if available) | | | | | [ ] |
- [ ] **Playwright cross-browser:** Run on chromium + firefox at minimum

## 6. Visual Regression (Optional) (Ngày 8–9)

- [ ] **Playwright screenshot compare:**
  - [ ] Home page — light + dark
  - [ ] Detail page — COMPLETED state
  - [ ] Detail page — NEEDS_REVIEW state
- [ ] **Baseline screenshots committed** or stored in CI artifact
- [ ] **If deferred:** Document as v1.1 improvement

## 7. Frontend Sign-off (Ngày 9–10)

- [ ] All Sprint 0–6 frontend checklists reviewed
- [ ] E2E tests pass against docker prod profile
- [ ] Lighthouse performance ≥ 85
- [ ] Browser matrix complete
- [ ] No critical UI bugs
- [ ] Coordinate with DevOps for release demo

---

## Deliverables

| Artifact | Path |
|----------|------|
| Playwright tests | `apps/web/e2e/` |
| Playwright config | `apps/web/playwright.config.ts` |
| Lighthouse report | `plan/frontend/LIGHTHOUSE-REPORT.md` |
| Browser matrix | `plan/frontend/BROWSER-MATRIX.md` |

## Sign-off

| Criteria | Pass |
|----------|------|
| E2E tests green | [ ] |
| Production docker build works | [ ] |
| Lighthouse performance ≥ 85 | [ ] |
| Browser matrix tested | [ ] |
