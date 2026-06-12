# BilgeAPI v1.2.0 — Production Release Evidence Report

Generated at: `2026-06-12T03:41:00Z`
Target Release Version: `v1.2.0`
Release Tag Candidate: `bilgeapi-v1.2.0`
Release Commit Hash: `c125b9944f3b84097a9e37550b480a087581a90d`

---

## 1. Migration Parity Status
We analyzed and resolved the SQLite local development migration warning by upgrading the local database schema to HEAD.
- **Previous Local SQLite Revision:** `32b9c1d4e5f6`
- **Alembic Head Revision:** `3b517c6cb58a` (added `repair_agent_promotions` table)
- **Action Performed:** `alembic upgrade head`
- **Result:** **PASSED / PARITY RESTORED**. Schema is up-to-date.

---

## 2. Test Verification & Coverage

| Test Module | Status | Passed | Coverage | Detail |
| :--- | :--- | :--- | :--- | :--- |
| **BilgeAPI Core** | **PASSED** | 257 | 82.88% | Above required 80% threshold |
| **UI Repair Suite** | **PASSED** | 70 | - | All checks passed |
| **Repair Agent Suite** | **PASSED** | 122 | - | All checks passed |
| **Agent Governance Suite** | **PASSED** | 18 | - | Phase 32B/C/E tests passed |
| **Total Tests** | **PASSED** | **467** | **82.88%** | **GO DECISION** |

---

## 3. OpenAPI Schema Export
- **Script:** `scripts/export_bilgeapi_openapi.py`
- **Result:** **SUCCESS**
- **Destination:** `docs/openapi/bilgeapi_openapi.json`

---

## 4. Frontend & Container Hardening

### Frontend Production Build
- **App:** `refine_control_plane`
- **Build Command:** `npm run build`
- **Result:** **PASSED / SUCCESS** (Turbopack production build succeeded without syntax or compilation errors)

### Docker Smoke Test
- **Container Build:** `docker compose build bilgeapi` -> **SUCCESS**
- **Container Launch:** `docker compose up -d bilgeapi` -> **STARTED / HEALTHY**
- **Smoke Suite:** `scripts/smoke_bilgeapi.py` -> **6/6 PASSED**
  - Health check endpoint: **PASSED** (HTTP 200)
  - Docs Swagger UI: **PASSED** (HTTP 200)
  - OpenAPI JSON endpoint: **PASSED** (HTTP 200)
  - Catalog listing (authenticated): **PASSED** (HTTP 200)
  - Incidents listing (authenticated): **PASSED** (HTTP 200)
  - Auth enforcement (unauthenticated -> 401/403): **PASSED**

---

## 5. Release Gate Scorecard & Decision

```text
Score: 100.00
Status: PASSED
Decision: GO
Warnings: 0
Blockers: 0
```

### Final Release Decision: **GO (PASSED)**
All security policies, dependency audits, module configurations, and endpoint mappings have passed with a perfect 100/100 scorecard. No waivers are required.
