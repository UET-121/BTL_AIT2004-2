# Sprint 0 — Scaffold (Tuần 1–2)

**Dates:** 2026-06-23 → 2026-07-06  
**Sprint Goal:** Vite + React + TS project chạy dev server, routing, Tailwind, API client skeleton.

---

## 1. Project Initialization (Ngày 1–2)

- [ ] **Verify/create Vite + React 19 + TS:** `apps/web/` with template react-ts
- [ ] **Package manager:** pnpm (lockfile [`pnpm-lock.yaml`](../../apps/web/pnpm-lock.yaml))
- [ ] **Install core dependencies:**
  - [ ] `@tanstack/react-router` ^1.94
  - [ ] `@tanstack/react-query` ^5.62
  - [ ] `@tanstack/router-plugin` — file-based routing
  - [ ] `tailwindcss` ^3.4, `postcss`, `autoprefixer`
  - [ ] `react-easy-crop` — for Sprint 1
- [ ] **Verify dev server:** `pnpm dev` → `http://localhost:5173`

## 2. Vite Configuration (Ngày 2)

- [ ] **[`vite.config.ts`](../../apps/web/vite.config.ts):**
  - [ ] TanStack Router plugin for file-based routes
  - [ ] **Dev proxy:**
    ```typescript
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/uploads': { target: 'http://localhost:8000', changeOrigin: true },
    }
    ```
  - [ ] Port: 5173
- [ ] **Test proxy:** API call to `/api/v1/recognition` reaches backend

## 3. Environment (Ngày 2–3)

- [ ] **Tạo `apps/web/.env.example`:**
  ```env
  # Empty = use Vite dev proxy
  VITE_API_URL=
  ```
- [ ] **Document:** Production build sets empty VITE_API_URL for same-origin nginx proxy
- [ ] **Type-safe env:** `import.meta.env.VITE_API_URL` in client.ts

## 4. TanStack Router Setup (Ngày 3–4)

- [ ] **File-based routing structure:**
  ```
  src/routes/
  ├── __root.tsx       # Layout, header, theme toggle
  ├── index.tsx        # Home page
  └── requests/
      └── $requestId.tsx  # Detail page
  ```
- [ ] **Root layout [`__root.tsx`](../../apps/web/src/routes/__root.tsx):**
  - [ ] Header with app title
  - [ ] Navigation links: Home
  - [ ] `<Outlet />` for child routes
- [ ] **Route tree generation:** `routeTree.gen.ts` auto-generated
- [ ] **404 handling:** Catch unknown routes (Sprint 5 polish)

## 5. TanStack Query Setup (Ngày 4)

- [ ] **[`main.tsx`](../../apps/web/src/main.tsx):**
  - [ ] `QueryClientProvider` wrapping app
  - [ ] Default options: `retry: 1`, `staleTime: 5000`
  - [ ] `RouterProvider` with generated route tree
- [ ] **Devtools (dev only):** `@tanstack/react-query-devtools`

## 6. Tailwind & Dark Mode (Ngày 4–5)

- [ ] **Tailwind config [`tailwind.config.js`](../../apps/web/tailwind.config.js):** Content paths, darkMode: 'class'
- [ ] **[`index.css`](../../apps/web/src/index.css):** `@tailwind base/components/utilities`
- [ ] **ThemeContext [`ThemeContext.tsx`](../../apps/web/src/contexts/ThemeContext.tsx):**
  - [ ] Toggle dark/light mode
  - [ ] Persist in `localStorage` key `theme`
  - [ ] Apply `dark` class to `<html>`
- [ ] **Verify toggle:** Switch theme → persists on reload

## 7. API Client Skeleton (Ngày 5–6)

- [ ] **[`client.ts`](../../apps/web/src/api/client.ts):**
  - [ ] Base URL: `import.meta.env.VITE_API_URL || ''`
  - [ ] Typed fetch wrapper with error handling
  - [ ] Functions stub: `uploadRecognition`, `getRecognition`, `listRecognitions`, `reprocessRecognition`
- [ ] **Error type:** `ApiError` with status and detail

## 8. TypeScript Types (Ngày 6–7)

- [ ] **[`types/index.ts`](../../apps/web/src/types/index.ts) — mirror backend:**
  - [ ] `RecognitionStatus`: NOT_STARTED | PENDING | COMPLETED | NEEDS_REVIEW | FAILED
  - [ ] `RecognitionRequest` with all fields including confidence, bbox
  - [ ] `RecognitionSubmitResponse`, `RecognitionListResponse`
  - [ ] `BoundingBox` interface
- [ ] **Fix current gap:** Add NEEDS_REVIEW to status union (currently missing)

## 9. Verification (Ngày 8–10)

- [ ] **`pnpm dev`** → app loads at localhost:5173
- [ ] **Dark mode toggle works**
- [ ] **Router navigates** between home and placeholder detail route
- [ ] **Proxy works:** `fetch('/api/v1/recognition')` hits backend (may 405 on GET — expected)
- [ ] **`pnpm build`** succeeds without errors
- [ ] **TypeScript strict:** `pnpm tsc --noEmit` passes

---

## Deliverables

| Artifact | Path |
|----------|------|
| Vite app | `apps/web/` |
| Router | `apps/web/src/routes/` |
| API client | `apps/web/src/api/client.ts` |
| Types | `apps/web/src/types/index.ts` |
| Env template | `apps/web/.env.example` |

## Dependencies

| From | Need |
|------|------|
| Backend Sprint 0 | API running for proxy test |
| DevOps Sprint 0 | `VITE_API_URL` in env docs |
