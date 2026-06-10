# Faz 31A — Acting Governor / Watchdog Core — Task List

## Planning
- [x] Add Faz 31A scope to `implementation_plan.md`.
- [x] Define read-only watchdog boundary and forbidden actions.

## Configuration
- [x] Add `BILGEAPI_WATCHDOG_ENABLED`.
- [x] Add `BILGEAPI_WATCHDOG_RISK_THRESHOLD`.
- [x] Add `BILGEAPI_WATCHDOG_AUTO_FINDING`.
- [x] Add `BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED`.

## Database & Migration
- [x] Add `SystemFindingModel`.
- [x] Add Alembic migration for `bilgeapi_system_findings`.

## Repository & Schemas
- [x] Add `SystemFindingRepository` interface.
- [x] Add Postgres implementation.
- [x] Add InMemory implementation.
- [x] Add `system_watchdog.py` schemas.

## Services
- [x] Implement `SystemSignalCollector`.
- [x] Implement `SystemRiskScorer`.
- [x] Implement `SystemFindingService`.
- [x] Implement `WatchdogEvidenceBuilder`.
- [x] Implement `ActingGovernorPolicy`.
- [x] Implement `SystemWatchdogService`.

## Routers & DI
- [x] Add watchdog DI dependencies.
- [x] Add `apps/bilgeapi/routers/system_watchdog.py`.
- [x] Register router in `apps/bilgeapi/main.py`.
- [x] Add watchdog modules/endpoints to release gate required lists.

## Tests
- [x] Add `tests/unit/bilgeapi/test_system_watchdog.py`.
- [x] Verify risk scoring.
- [x] Verify release gate blocker finding.
- [x] Verify ledger invalid finding path.
- [x] Verify finding dedupe and terminal no-reopen.
- [x] Verify forbidden actions.
- [x] Verify endpoint RBAC.
- [x] Verify payload redaction.
- [x] Verify disabled safe no-op.
- [x] Verify production human gate enforcement.

## Verification
- [x] Run Faz 31A unit tests.
- [x] Run BilgeAPI unit regression.
- [x] Run BilgeAPI unit + integration regression with coverage.
- [x] Apply Alembic migration to local databases.
- [x] Export OpenAPI.
- [x] Run release gate.
- [x] Build/restart Docker and smoke test.
- [x] Update `walkthrough.md`.
