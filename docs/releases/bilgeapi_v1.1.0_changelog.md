# BilgeAPI v1.1.0 Changelog

## Summary

BilgeAPI v1.1.0, v1.0 production gate uzerine enterprise API key management, tenant-aware quota, self-improvement workflow, safe Draft PR automation, sandbox verification, immutable review ledger, Ops Console ve AI-assisted patch suggestion katmanlarini ekler.

## Added

- DB-backed dynamic API key lifecycle:
  - `ApiKeyModel`
  - `/v1/admin/api-keys`
  - create/list/revoke/quota flows
- Tenant-aware quota and usage metering.
- Web research assisted self-improvement workflow:
  - research requests
  - evidence scoring
  - improvement proposals
  - audit reports
- Real web provider and evidence governance:
  - `SerperSearchProvider`
  - quality gate
  - confidence scoring
- Safe Draft PR automation:
  - PR draft records
  - mock/GitHub adapter boundary
  - human approval gate
- Sandbox verification and PR review gate:
  - `PrVerificationModel`
  - `SandboxPatchAnalyzer`
  - `PrReviewGateScorer`
- Reviewer feedback and patch revision workflow:
  - feedback records
  - patch revisions
  - revision verification
- Immutable Review Ledger:
  - ledger events
  - hash-chain integrity model
  - recent/integrity endpoints
- Ops Console:
  - API keys
  - quotas
  - research/proposals
  - PR drafts/verifications
  - feedback/revisions
  - immutable review ledger
  - AI patch suggestions
- AI-assisted patch suggestion workflow:
  - guarded mock/default provider
  - provider allow flag
  - context redaction
  - deterministic `prompt_hash`
  - sandbox verification integration
  - ledger event integration

## Security Guarantees

- Plaintext API keys are not persisted.
- Secrets and API keys are redacted from AI patch suggestion context.
- Real AI provider execution is disabled unless explicitly enabled by config.
- AI suggestions are draft-only and never mutate files, branches, commits, deployments or migrations.
- HIGH-risk patches cannot become direct `REVIEW_READY`.
- Draft PR creation remains human gated.
- Immutable review ledger records critical workflow transitions.

## Verification Evidence

Evidence bundle:

- `docs/releases/bilgeapi_v1.1.0/backend_regression.txt`
- `docs/releases/bilgeapi_v1.1.0/migration_audit.txt`
- `docs/releases/bilgeapi_v1.1.0/container_alembic_current.txt`
- `docs/releases/bilgeapi_v1.1.0/release_gate.txt`
- `docs/releases/bilgeapi_v1.1.0/docker_build.txt`
- `docs/releases/bilgeapi_v1.1.0/docker_smoke.txt`
- `docs/releases/bilgeapi_v1.1.0/frontend_build.txt`
- `docs/releases/bilgeapi_v1.1.0/frontend_smoke.txt`
- `docs/releases/bilgeapi_v1.1.0/openapi_freeze_check.txt`

Validated highlights:

- Backend regression: `206 passed`
- Coverage: `80.80%`
- Migration current/head: `a29c4f83b2d1 (head)`
- Release gate: `Score: 100.00`, `Status: PASSED`, `Warnings: 0`, `Blockers: 0`, `Decision: GO`
- Docker smoke: `6/6 passed`
- Frontend build: `/bilgeapi-ops` route generated

## Known Exclusions

Workspace contains unrelated dirty/staged files. These are documented in `docs/releases/bilgeapi_v1.1.0_workspace_audit.md` and excluded from the release commit.

