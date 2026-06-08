# Faz 28 - Immutable Review Ledger + Evidence Chain Sealing - Task List

## Planning
- [x] Review pasted Faz 28 requirements.
- [x] Add TDD tests for redaction, hash-chain verification, endpoint RBAC, and Phase 26 lifecycle event integration.

## Database & Models
- [x] Add `ReviewLedgerEntryModel` to `apps/bilgeapi/models/database.py`.
- [x] Create Alembic migration `f28a0b1c2d3e_add_review_ledger_entries.py`.
- [x] Keep JSON payload storage SQLite/Postgres compatible.

## Schemas
- [x] Create `apps/bilgeapi/schemas/review_ledger.py`.
- [x] Add response schemas for entries, chains, verification, append, and export payloads.

## Repositories
- [x] Add `ReviewLedgerRepository` interface.
- [x] Implement `InMemoryReviewLedgerRepository`.
- [x] Implement `PostgresReviewLedgerRepository`.

## Services
- [x] Implement `PayloadRedactor`.
- [x] Implement `CanonicalPayloadHasher`.
- [x] Implement `ReviewLedgerService`.
- [x] Implement `ReviewLedgerVerifier`.

## API Endpoints
- [x] Add `apps/bilgeapi/routers/review_ledger.py`.
- [x] Register router in `apps/bilgeapi/main.py`.
- [x] Add endpoints:
  - [x] `GET /v1/review-ledger/recent`
  - [x] `GET /v1/review-ledger/chains/{chain_id}`
  - [x] `GET /v1/review-ledger/chains/{chain_id}/verify`
  - [x] `GET /v1/review-ledger/chains/{chain_id}/export`
  - [x] `POST /v1/review-ledger/events`

## Lifecycle Integration
- [x] Add ledger events for research completion/failure.
- [x] Add ledger events for proposal creation.
- [x] Add ledger events for draft PR creation/failure.
- [x] Add ledger events for sandbox verification.
- [x] Add ledger events for reviewer feedback.
- [x] Add ledger events for patch revision creation and verification.

## Ops Console
- [x] Extend `apps/refine_control_plane/src/lib/bilgeapiOpsClient.ts` with review-ledger types and API functions.
- [x] Add Immutable Review Ledger tab to `/bilgeapi-ops`.
- [x] Add chain load, verify, export, recent ledger list, and payload preview UI.
- [x] Extend static UI contract test.

## Verification
- [x] Run target Phase 28 tests.
- [x] Run BilgeAPI unit/integration regression with coverage.
- [x] Export OpenAPI schema.
- [x] Run frontend production build.
- [x] Rebuild/recreate BilgeAPI Docker container and apply migrations.
- [x] Run release gate.
- [x] Run live smoke test.
- [x] Commit Faz 28 changes without unrelated staged files.
