# BilgeAPI Phase 31F Operations Hardening Evidence Report
Generated on: 2026-06-10T20:55:42.949542+00:00
Execution duration: 46.4s

## 1. Executive Summary

- **Hardening Phase Score**: **100.00 / 100.00**
- **Release Decision Status**: **GO / PASSED**
- **Docker Health Status**: `HEALTHY`

---

## 2. Scorecard & Release Gate Verification

### Release Gate Output Summary:
```

[94m=====================================================
      BilgeAPI v1.0 Production Release Gate Gatekeeper
=====================================================[0m
[CLI Release Gate] Running readiness audit...

--- AUDIT SCORECARD ---
Environment: DEVELOPMENT
Git SHA:     unknown
Version:     1.0.0
Score:       100.00
Status:      [92mPASSED[0m

--- CORE MODULES (24) ---
  apps.bilgeapi.config                    : [92mOK[0m
  apps.bilgeapi.auth                      : [92mOK[0m
  apps.bilgeapi.startup                   : [92mOK[0m
  apps.bilgeapi.main                      : [92mOK[0m
  apps.bilgeapi.adapters.webhook          : [92mOK[0m
  apps.bilgeapi.services.risk             : [92mOK[0m
  apps.bilgeapi.services.webhook          : [92mOK[0m
  apps.bilgeapi.services.audit            : [92mOK[0m
  apps.bilgeapi.services.diagnostic       : [92mOK[0m
  apps.bilgeapi.services.review_ledger    : [92mOK[0m
  apps.bilgeapi.services.ai_patch_suggestion: [92mOK[0m
  apps.bilgeapi.services.system_watchdog  : [92mOK[0m
  apps.bilgeapi.services.self_healing     : [92mOK[0m
  apps.bilgeapi.adapters.ai_patch_provider: [92mOK[0m
  apps.bilgeapi.models.database           : [92mOK[0m
  apps.bilgeapi.repositories.postgres     : [92mOK[0m
  apps.bilgeapi.repositories.memory       : [92mOK[0m
  apps.bilgeapi.routers.review_ledger     : [92mOK[0m
  apps.bilgeapi.routers.system_watchdog   : [92mOK[0m
  apps.bilgeapi.routers.self_healing      : [92mOK[0m
  apps.bilgeapi.schemas.review_ledger     : [92mOK[0m
  apps.bilgeapi.schemas.ai_patch_suggestion: [92mOK[0m
  apps.bilgeapi.schemas.system_watchdog   : [92mOK[0m
  apps.bilgeapi.schemas.self_healing      : [92mOK[0m

--- CORE ENDPOINTS (24) ---
  /health                                 : [92mVERIFIED_PRESENT[0m
  /docs                                   : [92mVERIFIED_PRESENT[0m
  /redoc                                  : [92mVERIFIED_PRESENT[0m
  /openapi.json                           : [92mVERIFIED_PRESENT[0m
  /v1/catalog                             : [92mVERIFIED_PRESENT[0m
  /v1/incidents                           : [92mVERIFIED_PRESENT[0m
  /v1/diagnostics                         : [92mVERIFIED_PRESENT[0m
  /v1/repair-requests                     : [92mVERIFIED_PRESENT[0m
  /v1/audit-events                        : [92mVERIFIED_PRESENT[0m
  /v1/webhook-deliveries                  : [92mVERIFIED_PRESENT[0m
  /v1/review-ledger/recent                : [92mVERIFIED_PRESENT[0m
  /v1/improvements/ai-suggestions/{suggestion_id}: [92mVERIFIED_PRESENT[0m
  /v1/watchdog/run                        : [92mVERIFIED_PRESENT[0m
  /v1/watchdog/status                     : [92mVERIFIED_PRESENT[0m
  /v1/watchdog/findings                   : [92mVERIFIED_PRESENT[0m
  /v1/watchdog/remediations               : [92mVERIFIED_PRESENT[0m
  /v1/watchdog/remediations/{attempt_id}  : [92mVERIFIED_PRESENT[0m
  /v1/watchdog/findings/{finding_id}/remediate: [92mVERIFIED_PRESENT[0m
  /v1/watchdog/runbooks                   : [92mVERIFIED_PRESENT[0m
  /v1/watchdog/runbooks/{runbook_id}/enable: [92mVERIFIED_PRESENT[0m
  /v1/watchdog/runbooks/{runbook_id}/disable: [92mVERIFIED_PRESENT[0m
  /v1/watchdog/emergency-recovery/run     : [92mVERIFIED_PRESENT[0m
  /v1/watchdog/findings/intake            : [92mVERIFIED_PRESENT[0m
  /v1/watchdog/external-recovery/report   : [92mVERIFIED_PRESENT[0m

--- WARNINGS (0) ---
  None

--- BLOCKERS (0) ---
  None

[92m[CLI Release Gate] Results persisted to DB. Record ID: rel_fffeb6d4[0m

[94m=====================================================
      RELEASE DECISION: [92mGO (PASSED)[0m
=====================================================[0m

```

---

## 3. Automated Test Targets & Integration Coverage

### Pytest Integration Outputs:
```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-8.3.5, pluggy-1.6.0
rootdir: E:\ai_company_faz12.1
configfile: pytest.ini
plugins: anyio-4.12.1, langsmith-0.7.6, asyncio-0.25.3, base-url-2.1.0, cov-7.0.0, mock-3.14.0, playwright-0.7.2
asyncio: mode=Mode.AUTO, asyncio_default_fixture_loop_scope=function
collected 2 items

tests\integration\test_bilgeapi_idempotency_live.py ..                   [100%]

============================== warnings summary ===============================
tests/integration/test_bilgeapi_idempotency_live.py::test_bridge_mapping_unique_constraint_sqlite
tests/integration/test_bilgeapi_idempotency_live.py::test_bridge_forward_concurrent_intake
  C:\Users\BİLGEHAN\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages\pytest_asyncio\plugin.py:867: DeprecationWarning: The event_loop fixture provided by pytest-asyncio has been redefined in
  E:\ai_company_faz12.1\tests\conftest.py:4
  Replacing the event_loop fixture with a custom implementation is deprecated
  and will lead to errors in the future.
  If you want to request an asyncio event loop with a scope other than function
  scope, use the "loop_scope" argument to the asyncio mark when marking the tests.
  If you want to return different types of event loops, use the event_loop_policy
  fixture.
  
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 2 passed, 2 warnings in 1.54s ========================

```

---

## 4. E2E Signal Intake & Bridge Idempotency Proof

### E2E Smoke Output:
```
[*] Starting E2E smoke checks for source: TASKFLOW_RUN_HARDENING:run_hardening_195c4c4f
[*] BilgeAPI URL: http://localhost:8100
[*] Submitting first intake signal via BilgeAPIBridge...
[+] First intake response: {'status': 'success', 'finding_id': 'sf_8475af17', 'created': True, 'deduped': False, 'mapping_id': 'map_68c647e4d127'}
[*] Submitting second intake signal (raw HTTP to trigger server deduplication)...
[+] Second response (server deduplicated): {'status': 'success', 'finding_id': 'sf_8475af17', 'created': False, 'deduped': True, 'terminal': False}
[*] Connecting to database for verifying records...
[+] Found 1 mapping record(s) in database.
[+] Found 1 finding record(s) in database.
[+] Found 2 review ledger entries for finding sf_8475af17.
[+] Ledger events in order: ['SYSTEM_FINDING_CREATED', 'SYSTEM_FINDING_DEDUPED']
[SUCCESS] All E2E smoke and idempotency checks passed successfully!

```

---

## 5. Supervisor Spool & Flush Proof (Non-Destructive)

### Supervisor Recovery Output:
```
Health check failed for http://localhost:9999/health: <urlopen error [WinError 10061] Hedef makine etkin olarak reddettiğinden bağlantı kurulamadı>
[*] Starting supervisor recovery check.
[*] Destructive real restart test: False
[*] Simulating BilgeAPI down state using invalid URL...
Starting recovery attempt #1 for service: bilgeapi...
[+] Recovery attempt spooled: {'event_type': 'SUPERVISOR_RECOVERY_COMPLETED', 'timestamp': '2026-06-10T20:55:05.027689+00:00', 'service_name': 'bilgeapi', 'attempt_no': 1, 'output': "MOCK: Command ['docker', 'compose', 'restart', 'bilgeapi'] executed successfully.", 'error': '', 'status': 'success'}
[*] Simulating BilgeAPI up state using healthy URL...
[*] Executing recovery cycle on healthy endpoint to trigger flush...
Successfully flushed 1 spooled events to BilgeAPI.
[+] Spool file successfully flushed and cleared.
[*] Connecting to database to verify spooled events in Review Ledger...
[+] Found 3 supervisor recovery entries in ledger.
[+] Verified latest ledger entry: seq=3, type=SUPERVISOR_RECOVERY_COMPLETED
[SUCCESS] Supervisor recovery and spooling checks passed successfully!

```

---

## 6. Review Ledger Corruption & Human Gate Block Proof

### Ledger Corruption Output:
```
[*] Starting ledger corruption check on isolated chain: test_chain_corrupt_4e4b70410fef
[*] Creating 3 valid ledger events to build the test chain...
[*] Verifying chain is initially valid...
[+] Initial verify response: {'chain_id': 'test_chain_corrupt_4e4b70410fef', 'valid': True, 'entry_count': 3, 'head_hash': '6ff138926466f92c6d8db04dcfcaa87d5618d5ca27db2392f8dbaaae57f6b45b', 'issues': []}
[+] assert_approval_allowed passed on valid ledger.
[*] Corrupting the chain in DB (modifying previous_hash of the second entry)...
[+] Corrupted previous_hash in database.
[*] Verifying that corrupted chain is detected and blocked...
[+] Post-corruption verify response: {'chain_id': 'test_chain_corrupt_4e4b70410fef', 'valid': False, 'entry_count': 3, 'head_hash': '6ff138926466f92c6d8db04dcfcaa87d5618d5ca27db2392f8dbaaae57f6b45b', 'issues': [{'type': 'previous_hash_mismatch', 'entry_id': 'rle_f90a06d4', 'expected': '6f1d54ea70cc67bbf4d70a1e545942731057d97bd5ffcedf6e4f6865e57f74de', 'actual': 'corrupted_previous_hash_bogus_12345'}, {'type': 'event_hash_mismatch', 'entry_id': 'rle_f90a06d4', 'expected': 'a7c7dcc230df5bd57327e031d0f178e08d9e5334d5062908a41ad681e9346bea', 'actual': '168c5c1d75515e608eb35695827d4920773869c68bf99a306411cbf5517fe1bc'}]}
[*] Asserts that assert_approval_allowed raises ValueError on corrupted chain...
23:55:12  ERROR     [repair.bilgeapi_human_gate_context] [no-trace] Approval blocked: Ledger chain test_chain_corrupt_4e4b70410fef is corrupted. Issues: {'type': 'previous_hash_mismatch', 'entry_id': 'rle_f90a06d4', 'expected': '6f1d54ea70cc67bbf4d70a1e545942731057d97bd5ffcedf6e4f6865e57f74de', 'actual': 'corrupted_previous_hash_bogus_12345'}; {'type': 'event_hash_mismatch', 'entry_id': 'rle_f90a06d4', 'expected': 'a7c7dcc230df5bd57327e031d0f178e08d9e5334d5062908a41ad681e9346bea', 'actual': '168c5c1d75515e608eb35695827d4920773869c68bf99a306411cbf5517fe1bc'}
[+] Success: assert_approval_allowed successfully raised ValueError: Approval blocked: Ledger chain integrity verification failed. Issues: {'type': 'previous_hash_mismatch', 'entry_id': 'rle_f90a06d4', 'expected': '6f1d54ea70cc67bbf4d70a1e545942731057d97bd5ffcedf6e4f6865e57f74de', 'actual': 'corrupted_previous_hash_bogus_12345'}; {'type': 'event_hash_mismatch', 'entry_id': 'rle_f90a06d4', 'expected': 'a7c7dcc230df5bd57327e031d0f178e08d9e5334d5062908a41ad681e9346bea', 'actual': '168c5c1d75515e608eb35695827d4920773869c68bf99a306411cbf5517fe1bc'}
[*] Cleaning up all database entries for test chain: test_chain_corrupt_4e4b70410fef
[+] Database cleanup complete.
[SUCCESS] Ledger corruption verification checks passed successfully!

```

---

## 7. 6/6 Smoke Test Results

### Smoke Test Output:
```

======================================================================
  BilgeAPI Smoke Test - http://localhost:8100
======================================================================
  [OK]   Health                              GET /health               HTTP 200
  [OK]   Docs (Swagger UI)                   GET /docs                 HTTP 200
  [OK]   OpenAPI JSON                        GET /openapi.json         HTTP 200
  [OK]   Catalog (with key)                  GET /v1/catalog           HTTP 200
  [OK]   Incidents list (with key)           GET /v1/incidents         HTTP 200
  [OK]   Auth enforcement (no key -> 401/403) GET /v1/incidents         HTTP 401
----------------------------------------------------------------------
  Result: 6/6 passed - ALL PASSED
======================================================================


```

---

## 8. OpenAPI Schema Export Status

### OpenAPI Export Output:
```
Successfully exported OpenAPI schema to: E:\ai_company_faz12.1\docs\openapi\bilgeapi_openapi.json

```

---

## 9. Refine Frontend Static Build Verification

- **Build Exit Code Status**: `SUCCESS`

### Build Output Summary:
```

> refine_control_plane@0.1.0 build
> next build

â–² Next.js 16.2.3 (Turbopack)
- Environments: .env.local

  Creating an optimized production build ...
âœ“ Compiled successfully in 6.7s
  Running TypeScript ...
  Finished TypeScript in 9.7s ...
  Collecting page data using 19 workers ...
  Generating static pages using 19 workers (0/73) ...
  Generating static pages using 19 workers (18/73) 
  Generating static pages using 19 workers (36/73) 
  Generating static pages using 19 workers (54/73) 
âœ“ Generating static pages using 19 workers (73/73) in 489ms
  Finalizing page optimization ...

Route (app)
â”Œ Æ’ /
â”œ Æ’ /_not-found
â”œ Æ’ /approvals
â”œ Æ’ /approvals/[id]
â”œ Æ’ /audit
â”œ Æ’ /axiology
â”œ Æ’ /axiology/[id]
â”œ Æ’ /bilgeapi-ops
â”œ Æ’ /calibrations
â”œ Æ’ /compliance
â”œ Æ’ /compliance/audit-bundles
â”œ Æ’ /costs
â”œ Æ’ /evolution
â”œ Æ’ /federation
â”œ Æ’ /fleet
â”œ Æ’ /fleet/agents
â”œ Æ’ /fleet/operations
â”œ Æ’ /governance/approvals
â”œ Æ’ /governance/approvals/[id]
â”œ Æ’ /governance/audit
â”œ Æ’ /governance/compliance
â”œ Æ’ /governance/compliance/audit-bundles
â”œ Æ’ /governance/escalations
â”œ Æ’ /governance/incidents
â”œ Æ’ /governance/incidents/[id]
â”œ Æ’ /governance/lineage
â”œ Æ’ /governance/ops/launch-gates
â”œ Æ’ /governance/proposals
â”œ Æ’ /governance/safety
â”œ Æ’ /governor
â”œ Æ’ /governor/[id]
â”œ Æ’ /governor/alerts
â”œ Æ’ /governor/alerts/[id]
â”œ Æ’ /governor/conflicts
â”œ Æ’ /governor/drifts
â”œ Æ’ /governor/drifts/[id]
â”œ Æ’ /governor/drills
â”œ Æ’ /governor/escalations
â”œ Æ’ /governor/federated
â”œ Æ’ /governor/observability
â”œ Æ’ /governor/outcomes
â”œ Æ’ /governor/proof
â”œ Æ’ /governor/proof/events
â”œ Æ’ /governor/proof/snapshots
â”œ Æ’ /governor/proof/snapshots/[id]
â”œ Æ’ /governor/resilience
â”œ Æ’ /governor/scorecard
â”œ Æ’ /identity
â”œ Æ’ /improvements
â”œ Æ’ /incidents
â”œ Æ’ /incidents/[id]
â”œ Æ’ /learning/adaptation-candidates
â”œ Æ’ /learning/fingerprints
â”œ Æ’ /learning/fingerprints/[id]
â”œ Æ’ /learning/negative-patterns
â”œ Æ’ /learning/strategy-memory
â”œ Æ’ /login
â”œ Æ’ /mcp-hub
â”œ Æ’ /meeting-room
â”œ Æ’ /mesh
â”œ Æ’ /ops/handover-status
â”œ Æ’ /ops/launch-gates
â”œ Æ’ /policy-proposals
â”œ Æ’ /project-factory
â”œ Æ’ /project-factory/[project_id]
â”œ Æ’ /prompt-studio
â”œ Æ’ /proof/events
â”œ Æ’ /proof/snapshots
â”œ Æ’ /proof/snapshots/[id]
â”œ Æ’ /repair-lab
â”œ Æ’ /repair-lab/improvements
â”œ Æ’ /repair-memory
â”œ Æ’ /safety
â”œ Æ’ /self-tuning
â”œ Æ’ /self-tuning/scoped
â”œ Æ’ /system-health
â”œ Æ’ /training
â”œ Æ’ /ui-repair
â”œ Æ’ /verifiers
â”œ Æ’ /workflows
â”œ Æ’ /workflows/[id]
â”” Æ’ /workflows/create


Æ’  (Dynamic)  server-rendered on demand


```

---

## 10. Safe Operation & Runtime Compliance Check

> [!NOTE]
> All hardening tests were successfully run on isolated test chains or dry-run mocked environments.
> No new runtime routes, models, or feature additions were introduced during Phase 31F.
