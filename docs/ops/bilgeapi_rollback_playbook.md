# BilgeAPI v1.2.0 — Production Rollback Playbook

This runbook outlines the steps to safely rollback BilgeAPI containers and database schema state in the event of post-deployment failures or service degradation.

---

## 1. Rollback Trigger Criteria

A rollback must be initiated immediately if any of the following occur within 24 hours of deployment:
1. **Smoke Test Failure:** The smoke test suite (`scripts/smoke_bilgeapi.py`) fails (score < 6/6).
2. **High Error Rates:** Sustained `5xx` response rates exceed **1%** over a 15-minute window.
3. **Database Connectivity Failures:** Core database operations timeout or fail continuously.
4. **Service Unhealthy:** Container healthcheck fails, causing automatic restarts.

---

## 2. Container Service Rollback

To revert the application version to the previous stable release:

### Step 1: Identify Last Stable Version
* Target Release Candidate: **`v1.2.0`** (tag: `bilgeapi-v1.2.0`)
* Previous Stable Release: **`v1.1.0`** (tag: `bilgeapi-v1.1.0`)

### Step 2: Revert Container Image/Code
If running in Docker Compose mode:
```powershell
# 1. Stop the failing container
docker compose down bilgeapi

# 2. Checkout the previous stable release tag
git checkout tags/bilgeapi-v1.1.0

# 3. Rebuild and launch the stable container image
docker compose build bilgeapi
docker compose up -d bilgeapi
```

---

## 3. Database Schema Rollback

> [!CAUTION]
> Database rollback should only be executed if the schema changes made in v1.2.0 are incompatible with the v1.1.0 codebase, or if they caused severe data-layer errors.

### Method A: Alembic Downgrade (Soft Rollback)
If the database connection is healthy, downgrade the schema by one step:
```powershell
# Verify current revision
py -3.13 -m alembic current

# Downgrade to previous revision (e.g., target revision before 3b517c6cb58a)
py -3.13 -m alembic downgrade -1
```

### Method B: Database Restore from Backup (Hard Rollback)
If migration failed or corrupted the database state:
```powershell
# 1. Stop application containers to prevent active database writes
docker compose stop bilgeapi

# 2. Backup the corrupted database for diagnostics
cp runtime/data/cortex_local_v2.db runtime/data/cortex_local_v2.db.failed

# 3. Restore the pre-deployment database snapshot
cp runtime/data/cortex_local_v2.db.bak runtime/data/cortex_local_v2.db

# 4. Start the previous stable version container
docker compose start bilgeapi
```

---

## 4. Post-Rollback Verification

Immediately run the smoke test suite to verify system integrity:
```powershell
$env:PYTHONUTF8='1'
py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key <PREVIOUS_STABLE_API_KEY>
```
Verify that:
- Core endpoints return `HTTP 200`.
- System healthcheck passes.
- Logs are clean of database schema exceptions.
