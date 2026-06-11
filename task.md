# Unified Faz 31/32 — Autonomous Governance Task List

## Repo Reality Check

- [x] Confirm `system_watchdog` router is included in `apps/bilgeapi/main.py`.
- [x] Confirm `self_healing` router is included in `apps/bilgeapi/main.py`.
- [x] Confirm release gate requires watchdog/self-healing modules.
- [x] Confirm release gate requires watchdog/self-healing endpoints.
- [x] Confirm OpenAPI includes `/v1/watchdog/*` endpoints.

## Watchdog Core

- [x] Verify `SystemFindingModel` exists.
- [x] Verify finding dedupe and lifecycle tests pass.
- [x] Verify risk scorer tests pass.
- [x] Verify watchdog admin/operator RBAC tests pass.

## Controlled Self-Healing

- [x] Verify remediation runbook and attempt models exist.
- [x] Verify self-healing config flags exist.
- [x] Verify forbidden actions are blocked by `SelfHealingPolicy`.
- [x] Verify `HIGH` risk findings require human gate.
- [x] Verify `CRITICAL` emergency recovery is limited to liveness recovery actions.
- [x] Verify self-healing executor uses controlled handlers and does not run shell commands.

## Regression

- [x] Run targeted watchdog/self-healing tests:
  `py -3.13 -m pytest tests/unit/bilgeapi/test_system_watchdog.py tests/unit/bilgeapi/test_self_healing.py -v`
- [x] Run full BilgeAPI unit/integration regression with coverage:
  `py -3.13 -m pytest tests/unit/bilgeapi tests/integration/bilgeapi --cov=apps/bilgeapi --cov-report=xml --cov-report=term-missing`
- [x] Confirm target coverage is >= 80%.

## Release Verification

- [x] Export OpenAPI:
  `py -3.13 scripts/export_bilgeapi_openapi.py`
- [x] Run release gate:
  `py -3.13 scripts/run_release_gate.py`
- [x] Build BilgeAPI Docker image:
  `docker compose build bilgeapi`
- [x] Restart BilgeAPI container:
  `docker compose up -d bilgeapi`
- [x] Run smoke test:
  `$env:PYTHONUTF8='1'; py -3.13 scripts/smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key dev-test-key-001`

## Documentation & Commit

- [x] Rewrite `implementation_plan.md` as the unified Faz 31/32 plan.
- [x] Update `walkthrough.md` with verified outputs.
- [x] Stage only relevant files.
- [x] Commit with a scoped message.
