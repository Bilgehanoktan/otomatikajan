# BilgeAPI v1.2.0 — Production Hypercare Evidence Report

Generated at: `2026-06-12T20:05:00Z`
Target Release Version: `v1.2.0`
Phase: **Phase 35 — Production Hypercare & Runtime Version Alignment**

---

## 1. Runtime Version Alignment Verification
We resolved the health endpoint version metadata issue where the service returned `"version": "1.0.0"`. The version configuration has been unified under `Settings.BILGEAPI_VERSION`.

### API Health Check Response
- **Endpoint:** `GET http://127.0.0.1:8100/health`
- **Output:**
  ```json
  {"status":"ok","service":"bilgeapi","version":"1.2.0","auth_mode":"api_key","skill_registry":"HEALTHY"}
  ```
- **Parity Status:** **PASSED** (Dynamic version reads correctly as `1.2.0`).

### Automated Unit Tests
- **Test File:** `tests/unit/bilgeapi/test_health_version.py`
- **Tests run:** 2
- **Status:** **PASSED (100% success)**
- **Regression Suite:** `py -3.13 -m pytest tests/unit/bilgeapi -v` -> **265 passed, 1 skipped (0 failures)**.

---

## 2. Container Status & Health Check
We verified that the docker compose runtime is stable and healthy.

- **Command:** `docker compose ps`
- **Output Status:**
  * `ai_company_faz121-bilgeapi-1`: **Up (healthy)**
  * `ai_company_faz121-db-1`: **Up (healthy)**
  * `ai_company_faz121-redis-1`: **Up (healthy)**
  * `deerflow-bridge`: **Up (healthy)**

---

## 3. Log Inspection & Safety Audits

We inspected the active server logs (`docker compose logs bilgeapi`) and verified:
1. **Zero Critical Errors:** No connection timeouts, Postgresql connection drops, or runtime exceptions found.
2. **Watchdog Telemetry Active:** Meta-Governor logs confirm that startup validation passed successfully.
3. **No Safety Policy Violations:**
   * `BILGEAPI_SELF_HEALING_ENABLED` evaluates to `false`. Zero autonomous remediations were executed.
   * `BILGEAPI_EXTERNAL_AGENTS_ENABLED` evaluates to `false`. Zero external agent promotion/run requests occurred without authorization.

---

## 4. Hypercare Smoke Verification
We executed the smoke test suite using the production-safe API key `production-smoke-auth-key-2026`:

* **Command:** `py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key production-smoke-auth-key-2026`
* **Smoke Status:** **6/6 PASSED - ALL PASSED**
