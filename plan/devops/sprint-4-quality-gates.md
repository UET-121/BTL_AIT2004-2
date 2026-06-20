# Sprint 4 — Quality Gates (Tuần 9–10)

**Dates:** 2026-08-18 → 2026-08-31  
**Sprint Goal:** Pre-commit hooks và local CI script chạy lint + test + docker build.

---

## 1. Pre-commit Configuration (Ngày 1–3)

- [ ] **Tạo `.pre-commit-config.yaml` tại repo root**
- [ ] **Backend hooks:**
  - [ ] `ruff check` — lint Python
  - [ ] `ruff format --check` — format check
  - [ ] `mypy apps/api/app` — type check (gradual, allow untyped initially)
- [ ] **Frontend hooks:**
  - [ ] `eslint` — lint TS/TSX
  - [ ] `prettier --check` — format check
- [ ] **General hooks:**
  - [ ] `trailing-whitespace`
  - [ ] `end-of-file-fixer`
  - [ ] `check-yaml`
  - [ ] `check-added-large-files` — max 1MB (exclude DVC pointers)
- [ ] **Install doc:** `pip install pre-commit && pre-commit install`
- [ ] **Verify:** Introduce intentional lint error → hook blocks commit

## 2. Backend Lint Config (Ngày 2–3)

- [ ] **Ruff config in `pyproject.toml` or `ruff.toml`:** Line length 100, target py312
- [ ] **Mypy config:** `ignore_missing_imports = true` for cv2, easyocr initially
- [ ] **Exclude:** `migrations/`, `__pycache__/`, `.venv/`
- [ ] **Makefile target:** `make lint` in apps/api

## 3. Frontend Lint Config (Ngày 3–4)

- [ ] **ESLint config verify:** Existing or add `@eslint/js` + typescript-eslint
- [ ] **Prettier config:** `.prettierrc` — singleQuote, trailingComma es5
- [ ] **package.json scripts:** `"lint": "eslint src"`, `"format:check": "prettier --check src"`
- [ ] **Makefile target:** `make lint` in apps/web

## 4. Local CI Script (Ngày 4–7)

- [ ] **Tạo `scripts/ci.sh`:** Single entry point for quality gates
- [ ] **Step 1 — Backend lint:** `cd apps/api && ruff check . && ruff format --check .`
- [ ] **Step 2 — Backend tests:** `cd apps/api && pytest tests/ -v --cov=app --cov-fail-under=50` (raise to 70 Sprint 6)
- [ ] **Step 3 — Frontend lint:** `cd apps/web && pnpm lint`
- [ ] **Step 4 — Frontend build:** `cd apps/web && pnpm build`
- [ ] **Step 5 — Docker build:** `docker compose build app worker web` (no start)
- [ ] **Step 6 — Dependency audit:** `pip audit` + `pnpm audit` (warn only, don't fail initially)
- [ ] **Exit on first failure:** Set `set -e` in bash script
- [ ] **Makefile target:** `make ci` at root
- [ ] **Runtime target:** Complete in < 15 minutes on dev machine

## 5. Docker Build Cache Optimization (Ngày 7–8)

- [ ] **API Dockerfile layer order:** requirements.txt → pip install → copy app code
- [ ] **Use BuildKit cache mount:** `RUN --mount=type=cache,target=/root/.cache/pip pip install`
- [ ] **Web Dockerfile layer order:** package.json → pnpm install → copy src → build
- [ ] **Measure rebuild time:** Code-only change rebuild < 2 min
- [ ] **Document:** `DOCKER_BUILDKIT=1 docker compose build`

## 6. SBOM & Dependency Audit (Ngày 8–9)

- [ ] **pip audit:** Run in CI script, log vulnerabilities
- [ ] **pnpm audit:** Run in CI script, log vulnerabilities
- [ ] **Pin critical deps:** Document policy for pinning fastapi, sqlalchemy, etc.
- [ ] **Dependabot placeholder:** Document future GitHub Dependabot config

## 7. CI Documentation (Ngày 9–10)

- [ ] **DevOps README section:** "Running CI locally" with `make ci`
- [ ] **Pre-commit bypass policy:** Never on main; `--no-verify` requires justification
- [ ] **Fix all lint errors:** CI green on current codebase before sprint review
- [ ] **Sprint Review demo:** Run `make ci` live, show green output

---

## Deliverables

| Artifact | Path |
|----------|------|
| Pre-commit config | `.pre-commit-config.yaml` |
| CI script | `scripts/ci.sh` |
| Ruff/mypy config | `pyproject.toml` or equivalent |
| Root Makefile `ci` target | `Makefile` |

## Dependencies

| From | Need |
|------|------|
| Backend Sprint 4+ | pytest tests exist |
| Backend Sprint 5 | Coverage target increase |

## Stretch Goals

- [ ] **GitHub Actions workflow:** Mirror `scripts/ci.sh` for PR checks
- [ ] **Coverage badge:** Generate coverage report artifact
