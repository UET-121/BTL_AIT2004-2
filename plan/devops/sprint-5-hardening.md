# Sprint 5 — Hardening (Tuần 11–12)

**Dates:** 2026-09-01 → 2026-09-14  
**Sprint Goal:** Resource limits, secrets management, backup/restore, disaster recovery documented.

---

## 1. Docker Resource Limits (Ngày 1–2)

- [ ] **API service limits:** `deploy.resources.limits.memory: 512M`, `cpus: '1.0'`
- [ ] **Worker service limits:** `deploy.resources.limits.memory: 2G`, `cpus: '2.0'` (EasyOCR)
- [ ] **Web service limits:** `deploy.resources.limits.memory: 128M`
- [ ] **DB service limits:** `deploy.resources.limits.memory: 512M`
- [ ] **Redis limits:** `deploy.resources.limits.memory: 256M`
- [ ] **Document Compose v3 syntax vs Swarm:** Note limits work in Swarm; for desktop use `mem_limit` alternative
- [ ] **Test OOM behavior:** Worker exceeds limit → graceful fail with log message

## 2. Secrets Management (Ngày 2–4)

- [ ] **Verify `.env` in `.gitignore`:** Root and apps/api, apps/web
- [ ] **Never commit secrets doc:** Add to DevOps README security section
- [ ] **Document `python-dotenv` loading order:** `.env` → environment variables
- [ ] **Optional direnv:** `.envrc.example` with `dotenv .env`
- [ ] **Docker secrets placeholder:** Document `secrets:` block for future Swarm/K8s
- [ ] **Rotate credentials guide:** How to change POSTGRES_PASSWORD safely
- [ ] **Audit repo history:** `git log -p -- .env` — confirm no leaks

## 3. Database Backup (Ngày 4–6)

- [ ] **Tạo `scripts/backup-db.sh`:**
  - [ ] Accept output dir arg, default `data/backups/`
  - [ ] Filename: `plate_recognition_YYYYMMDD_HHMMSS.sql.gz`
  - [ ] Use `docker compose exec -T db pg_dump -U postgres plate_recognition | gzip`
  - [ ] Verify exit code, print file size
- [ ] **Makefile target:** `make backup-db`
- [ ] **Retention policy:** Keep last 7 backups, auto-delete older (optional in script)
- [ ] **Schedule doc:** Recommend daily backup cron for long-running local instances

## 4. Uploads Backup (Ngày 6–7)

- [ ] **Tạo `scripts/backup-uploads.sh`:** Tar `uploads/` or docker volume
- [ ] **Coordinate with volume name:** `uploads_data` docker volume → `docker run --rm -v uploads_data:/data -v $(pwd)/data/backups:/backup alpine tar czf ...`
- [ ] **Makefile target:** `make backup-all` — db + uploads
- [ ] **Document size expectations:** Typical upload storage growth

## 5. Disaster Recovery (Ngày 7–9)

- [ ] **Tạo `plan/devops/DISASTER-RECOVERY.md`:**
  - [ ] **Scenario 1 — DB corruption:** Stop app → restore from backup → migrate
  - [ ] **Scenario 2 — Lost uploads volume:** Restore tar → verify image_url paths
  - [ ] **Scenario 3 — Full data/ wipe:** Step-by-step rebuild from backups
  - [ ] **Scenario 4 — Model files missing:** `make models` → restart worker
- [ ] **Restore script:** `scripts/restore-db.sh` — `gunzip | psql` with confirmation prompt
- [ ] **Test restore:** Backup → drop table → restore → verify row count
- [ ] **RTO/RPO targets (local):** RTO < 30 min, RPO = last backup (document)

## 6. Production Profile Hardening (Ngày 9–10)

- [ ] **Compose profile `prod`:**
  - [ ] No source code volume mounts
  - [ ] No Flower service
  - [ ] No exposed DB/Redis ports (internal network only)
  - [ ] `DEBUG=false`, `LOG_LEVEL=INFO`
- [ ] **Usage:** `docker compose --profile prod up -d`
- [ ] **Compare dev vs prod table:** Document differences in DevOps README
- [ ] **Verify prod profile startup:** All services healthy

---

## Deliverables

| Artifact | Path |
|----------|------|
| Backup script | `scripts/backup-db.sh` |
| Restore script | `scripts/restore-db.sh` |
| DR doc | `plan/devops/DISASTER-RECOVERY.md` |
| Prod compose profile | `docker-compose.yml` |

## Verification

- [ ] `make backup-db` creates valid gzip SQL dump
- [ ] Restore script recovers deleted test row
- [ ] Prod profile starts without dev-only services

## Stretch Goals

- [ ] **Automated backup in compose:** Sidecar cron container
- [ ] **Upload virus scan placeholder:** Document ClamAV integration for production
