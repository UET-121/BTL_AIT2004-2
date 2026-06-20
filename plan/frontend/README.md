# Frontend Track — License Plate Recognition Redesign

## Scope

Nhánh Frontend chịu trách nhiệm React/Vite SPA: upload flow với crop, request list/detail, polling, confidence display, review workflow, UX polish, và E2E tests.

## Tech Stack

- Vite 6 + React 19 + TypeScript
- TanStack Router (file-based routing)
- TanStack Query (data fetching, polling, mutations)
- Tailwind CSS 3 + dark mode
- react-easy-crop (client-side plate cropping)

## Dependencies với các nhánh khác

| Nhánh | Frontend cần từ họ | Frontend cung cấp cho họ |
|-------|--------------------|--------------------------|
| **Backend** | REST API stable, OpenAPI | Upload UX, crop compensation for detection |
| **DevOps** | nginx proxy, web docker service | Production build |
| **AI Engineer** | — | Client-side crop helps detection accuracy |

## Sprint Files

| Sprint | File | Theme |
|--------|------|-------|
| 0 | [sprint-0-scaffold.md](sprint-0-scaffold.md) | Vite scaffold |
| 1 | [sprint-1-upload-flow.md](sprint-1-upload-flow.md) | Upload + crop |
| 2 | [sprint-2-request-management.md](sprint-2-request-management.md) | List + status |
| 3 | [sprint-3-detail-confidence.md](sprint-3-detail-confidence.md) | Detail + confidence |
| 4 | [sprint-4-review-workflow.md](sprint-4-review-workflow.md) | Review + reprocess |
| 5 | [sprint-5-ux-polish.md](sprint-5-ux-polish.md) | Responsive + a11y |
| 6 | [sprint-6-release-qa.md](sprint-6-release-qa.md) | Playwright E2E |

## Key Code Paths

| Component | Path |
|-----------|------|
| Routes | [`apps/web/src/routes/`](../../apps/web/src/routes/) |
| Upload | [`apps/web/src/components/ImageUpload.tsx`](../../apps/web/src/components/ImageUpload.tsx) |
| Cropper | [`apps/web/src/components/ImageCropper.tsx`](../../apps/web/src/components/ImageCropper.tsx) |
| API client | [`apps/web/src/api/client.ts`](../../apps/web/src/api/client.ts) |
| Types | [`apps/web/src/types/index.ts`](../../apps/web/src/types/index.ts) |

## Known Gaps (Current → Target)

| Gap | Target sprint |
|-----|---------------|
| Missing NEEDS_REVIEW status | Sprint 2 |
| No confidence display | Sprint 3 |
| No bounding box overlay | Sprint 3 |
| Reprocess only for FAILED | Sprint 4 |

## Related Docs

- [API contracts](../_shared/05-api-contracts.md)
- [TypeScript types in contracts doc](../_shared/05-api-contracts.md#frontend-typescript-mirror)
