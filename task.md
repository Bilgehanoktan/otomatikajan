# Faz 30 - v1.1 Final Release Seal - Task List

## Planning

- [x] Add Faz 30 scope to `implementation_plan.md`.
- [x] Create/update this `task.md` checklist.
- [x] Confirm release baseline commit: `2069a368`.
- [x] Confirm release tag name: `bilgeapi-v1.1.0`.

## Workspace Cleanliness

- [x] Run `git status --short`.
- [x] Run `git diff --name-only`.
- [x] Run `git diff --cached --name-only`.
- [x] Identify unrelated dirty/staged files.
- [x] Exclude unrelated files from release commit.
- [x] Create `docs/releases/bilgeapi_v1.1.0_workspace_audit.md`.

## OpenAPI Freeze

- [x] Run `py -3.13 scripts/export_bilgeapi_openapi.py`.
- [x] Create `docs/openapi/bilgeapi_openapi.v1.1.0.json`.
- [x] Validate frozen OpenAPI JSON.
- [x] Confirm `/v1/improvements/*` endpoints exist.
- [x] Confirm `/v1/review-ledger/*` endpoints exist.
- [x] Confirm `/health` exists.

## Changelog

- [x] Create `docs/releases/bilgeapi_v1.1.0_changelog.md`.
- [x] Document Added features from Faz 14-29.
- [x] Document Security guarantees.
- [x] Document Verification evidence.
- [x] Document known exclusions/unrelated dirty files.

## Release Evidence Bundle

- [x] Create `docs/releases/bilgeapi_v1.1.0/`.
- [x] Save backend regression output.
- [x] Save coverage summary.
- [x] Save release gate output.
- [x] Save Docker smoke output.
- [x] Save frontend build output.
- [x] Save migration current/head output.
- [x] Save git status release output.
- [x] Save OpenAPI freeze check output.
- [x] Create `release_summary.md`.

## Backend Regression

- [x] Run full BilgeAPI unit/integration regression.
- [x] Confirm test count is at least `206 passed`.
- [x] Confirm coverage >= 80%.
- [x] Save output into release evidence bundle.

## Migration Audit

- [x] Run `py -3.13 scripts/verify_bilgeapi_migrations.py`.
- [x] Run container `alembic current`.
- [x] Confirm current/head is `a29c4f83b2d1`.
- [x] Save output into release evidence bundle.

## Release Gate

- [x] Run `py -3.13 scripts/run_release_gate.py`.
- [x] Confirm `Score: 100.00`.
- [x] Confirm `Status: PASSED`.
- [x] Confirm `Warnings: 0`.
- [x] Confirm `Blockers: 0`.
- [x] Confirm `Decision: GO`.
- [x] Save output into release evidence bundle.

## Docker & Smoke

- [x] Run `docker compose build bilgeapi`.
- [x] Run `docker compose up -d bilgeapi`.
- [x] Confirm `bilgeapi` container is healthy.
- [x] Run `scripts/smoke_bilgeapi.py`.
- [x] Confirm `6/6 passed`.
- [x] Smoke `GET /v1/review-ledger/recent`.
- [x] Smoke `GET /health`.
- [x] Save output into release evidence bundle.

## Frontend / Ops Console

- [x] Run `cmd /c npm.cmd run build` in `apps/refine_control_plane`.
- [x] Confirm `/bilgeapi-ops` route is generated.
- [x] Smoke `GET http://127.0.0.1:3100/bilgeapi-ops`.
- [x] Confirm Ops Console UI renders.
- [x] Confirm `Immutable Review Ledger` panel text exists.
- [x] Confirm `AI Patch Suggestions` panel text exists.
- [x] Save output into release evidence bundle.

## Checksum Manifest

- [x] Generate SHA-256 checksums for release evidence files.
- [x] Save `docs/releases/bilgeapi_v1.1.0/checksum_manifest.sha256`.
- [x] Verify manifest can be regenerated consistently.

## Final Commit

- [x] Stage only Faz 30 release files.
- [x] Commit: `chore: seal BilgeAPI v1.1.0 release`.
- [x] Confirm no unrelated files entered the commit.

## Final Tag

- [x] Create annotated tag: `bilgeapi-v1.1.0`.
- [x] Verify tag exists.
- [x] Verify tag points to final release commit.
- [x] Record tag hash in final release output.

## Final Seal

- [x] Confirm `git status` for Faz 30 target files is clean.
- [x] Confirm OpenAPI frozen file exists.
- [x] Confirm release evidence bundle exists.
- [x] Confirm release gate evidence exists.
- [x] Confirm final tag exists.
- [x] Update `walkthrough.md` with Faz 30 final release summary.
