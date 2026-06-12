# BilgeAPI v1.2.0 — Production Deployment Evidence Report

Generated at: `2026-06-12T19:55:00Z`
Target Release Version: `v1.2.0`
Phase: **Phase 34C — Production Human Gate, Deploy & Monitoring Seal**
Deployment Scope: **Local Production-Mode Simulation (External Public Production pending / out-of-scope)**

---

## 1. Pre-Deployment Compliance Status
Before launching to production, the release candidate passed all mandatory compliance checks:
* **Staging Environment Smoke Test:** **PASSED (6/6)**
* **Environment Safety Script (`verify_production_env_safety.py`):** **PASSED (0 Errors)**
* **Database Backup:** SQLite backup file hash registered and verified.
* **Human Gate Sign-off:** Staging logs and verification checklists reviewed and signed off.

---

## 2. Manual Database Migration Verification
The database schema upgrade was executed manually by the operator:
- **Command:** `py -3.13 -m alembic upgrade head`
- **Output:**
  ```text
  INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
  INFO  [alembic.runtime.migration] Will assume transactional DDL.
  INFO  [alembic.runtime.migration] Running upgrade  -> 3b517c6cb58a, add_repair_agent_promotions
  ```
- **Post-Upgrade Status:** **PASSED** (Schema successfully aligned to head revision `3b517c6cb58a`).

---

## 3. Production Deploy & Smoke Test Results
We verified that the production container was successfully rebuilt and started. We ran the smoke checks using a production-safe API key:

* **Production URL:** `http://localhost:8100` (Simulated Production host)
* **Production API Key:** `production-smoke-auth-key-2026`
* **Command:** `py -3.13 scripts/smoke_bilgeapi.py --base-url http://localhost:8100 --api-key production-smoke-auth-key-2026`

### Results:
| Check | Endpoint | Status | Detail |
| :--- | :--- | :--- | :--- |
| Health check | `GET /health` | **PASS** | HTTP 200 |
| Swagger UI | `GET /docs` | **PASS** | HTTP 200 |
| OpenAPI Schema | `GET /openapi.json` | **PASS** | HTTP 200 |
| Catalog Listing | `GET /v1/catalog` | **PASS** | HTTP 200 |
| Incidents Listing | `GET /v1/incidents` | **PASS** | HTTP 200 |
| Auth Enforcement | `GET /v1/incidents` (no key) | **PASS** | HTTP 401 |

**Production Smoke Status: 6/6 PASSED - ALL PASSED**

---

## 4. Production Release Tag & Seal
Following successful smoke test verification, the production annotated tag was created:
- **Annotated Tag Name:** `bilgeapi-v1.2.0-production`
- **Tag Description:** `BilgeAPI v1.2.0 production release build sealed and certified`
- **Release Status:** **GO / SEALED**
