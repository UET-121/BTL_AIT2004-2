# Sprint 5 — Hardening (Tuần 11–12)

**Dates:** 2026-09-01 → 2026-09-14

## Sprint Goal

Production-hardened local deploy; eval benchmark meets targets; UX polished; backup/restore works.

## Cross-team Dependencies

| Task | Owner | Blocker for |
|------|-------|-------------|
| Evaluation script + test set | AI | Release acceptance |
| Rate limiting + validation | Backend | Security hardening |
| Backup/restore scripts | DevOps | DR readiness |
| Coverage ≥ 70% | Backend | CI gate |
| Responsive + a11y | Frontend | Release quality |
| Load test report | Backend + DevOps | Performance baseline |

## Track Focus Summary

| Track | Key deliverables |
|-------|------------------|
| DevOps | Resource limits, backup, prod profile, DR doc |
| AI | 100-image eval, error analysis, acceptance gate |
| Backend | API hardening, coverage, extended health |
| Frontend | Mobile responsive, a11y, skeletons |

## Demo Script (Ngày 10)

1. `make evaluate` → char accuracy ≥ 90% (show report)
2. `make backup-db` → backup file created
3. Rate limit demo: 11 uploads → 429 on 11th
4. Mobile viewport demo: upload + list on phone size
5. Lighthouse a11y score ≥ 90
6. `docker compose --profile prod up -d` → prod-like stack
7. Restore DB from backup demo (optional)

## Definition of Done (Sprint 5)

- [ ] Char accuracy ≥ 90% on test set
- [ ] Review rate ≤ 25%
- [ ] Backup/restore verified
- [ ] Coverage ≥ 70%
- [ ] Mobile UX acceptable

## Acceptance Gate

| Metric | Target | Actual | Pass |
|--------|--------|--------|------|
| Char accuracy | ≥ 90% | | [ ] |
| Review rate | ≤ 25% | | [ ] |
| Backend coverage | ≥ 70% | | [ ] |

## Blockers Log

| Date | Blocker | Owner | Resolution |
|------|---------|-------|------------|
| | | | |

## Retrospective Notes

_Action items for Sprint 6_
