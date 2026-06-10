# Faz 31F — Governor Operations Hardening & E2E Seal — Task List

## Safety Checks & Constraints
- [x] Ledger corruption test uses isolated test chain or transaction rollback.
- [x] Supervisor recovery verification defaults to mock/dry-run mode.
- [x] Real container stop/restart requires explicit destructive flag.
- [x] Idempotency verification checks DB mapping count.
- [x] Evidence report includes release gate, smoke, OpenAPI and frontend build outputs.
- [x] Faz 31F does not add new runtime capability.

## Milestone 1 — E2E Smoke & Bridge Idempotency Live Verifications (Gate 1)
- [x] Create `scripts/ops/verify_governor_e2e.py` implementing E2E finding intake, ledger append, and database mapping check.
- [x] Implement database idempotency mapping verification (no duplicate findings, count = 1 in mappings).
- [x] Create `tests/integration/test_bilgeapi_idempotency_live.py` verifying database constraints on concurrent/duplicate signals.
- [x] Verify Gate 1: Run E2E and idempotency tests, confirm they pass.
- [x] Commit Gate 1: `feat: add governor e2e and idempotency verification`

## Milestone 2 — Supervisor Recovery & Ledger Corruption Dry-Runs (Gate 2)
- [x] Create `scripts/ops/verify_supervisor_recovery.py` with mock health/recovery checks (no destructive container restarts by default).
- [x] Add explicit `--destructive-real-restart-test` flag to supervisor recovery test script.
- [x] Create `scripts/ops/verify_ledger_corruption_block.py` using isolated test chain or transaction rollback to test corrupted ledger blocks.
- [x] Verify Gate 2: Run supervisor recovery and ledger corruption scripts, confirm they pass.
- [x] Commit Gate 2: `feat: add supervisor recovery and ledger corruption dry-run verification`

## Milestone 3 — Docker Smoke Test & Release Evidence Pack (Gate 3)
- [x] Create `scripts/ops/verify_phase31_hardening_evidence.py` to orchestrate all checks and export a comprehensive markdown report.
- [x] Run the evidence script and generate `docs/evidence/bilgeapi_phase31_hardening_evidence.md` with:
  - pytest targets and coverage outputs
  - Docker bilgeapi healthy check status
  - 6/6 smoke tests status
  - Release gate scorecard output (Score 100 / PASSED / GO)
  - OpenAPI schema export status
  - Refine frontend static build status
- [x] Verify Gate 3: Confirm evidence report compiles and accurately documents all outputs.
- [x] Commit Gate 3: `feat: add phase 31f operations evidence reporter`

## Final Seal (Final Gate)
- [x] Ensure no new runtime capabilities or destructiveness was introduced in Faz 31F.
- [x] Final tag and seal commit.
