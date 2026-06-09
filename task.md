# Faz 29 - AI-Assisted Patch Revision Suggestions - Task List

## Planning
- [x] Review pasted Faz 29 requirements.
- [x] Clean and update `implementation_plan.md`.
- [x] Add TDD tests for provider guardrails, redaction, prompt hashing, sandbox verification, ledger events, RBAC, and Ops Console contract.

## Configuration
- [x] Add `BILGEAPI_AI_PATCH_PROVIDER`.
- [x] Add `BILGEAPI_ALLOW_REAL_AI_PATCH`.
- [x] Add `BILGEAPI_AI_PATCH_MODEL`.
- [x] Add `BILGEAPI_AI_PATCH_MAX_CONTEXT_CHARS`.
- [x] Add `BILGEAPI_AI_PATCH_MAX_OUTPUT_CHARS`.

## Database & Migration
- [x] Add `AIPatchSuggestionModel`.
- [x] Add nullable `PrVerificationModel.ai_suggestion_id`.
- [x] Create Alembic migration for `bilgeapi_ai_patch_suggestions` and verification FK/index.

## Schemas
- [x] Create `apps/bilgeapi/schemas/ai_patch_suggestion.py`.

## Repositories
- [x] Add `AIPatchSuggestionRepository` interface.
- [x] Implement `InMemoryAIPatchSuggestionRepository`.
- [x] Implement `PostgresAIPatchSuggestionRepository`.

## Provider & Services
- [x] Create `apps/bilgeapi/adapters/ai_patch_provider.py`.
- [x] Implement `MockAIPatchProvider`.
- [x] Implement guarded `OpenAIPatchProvider` and `LocalAIPatchProvider`.
- [x] Create `apps/bilgeapi/services/ai_patch_suggestion.py`.
- [x] Implement redacted context builder.
- [x] Implement deterministic `prompt_hash`.
- [x] Enforce context/output size limits.
- [x] Implement generate, verify, accept, reject, and list flows.

## Verification Integration
- [x] Add `PrVerificationService.verify_ai_suggestion`.
- [x] Attach verification results to suggestions.
- [x] Preserve HIGH-risk downgrade rule.
- [x] Write AI suggestion events to immutable review ledger.

## API Endpoints
- [x] Add `POST /v1/improvements/pr-drafts/{pr_draft_id}/ai-suggestions`.
- [x] Add `GET /v1/improvements/pr-drafts/{pr_draft_id}/ai-suggestions`.
- [x] Add `GET /v1/improvements/ai-suggestions/{suggestion_id}`.
- [x] Add `POST /v1/improvements/ai-suggestions/{suggestion_id}/verify`.
- [x] Add `POST /v1/improvements/ai-suggestions/{suggestion_id}/accept-for-review`.
- [x] Add `POST /v1/improvements/ai-suggestions/{suggestion_id}/reject`.

## Ops Console
- [x] Add AI suggestion client methods.
- [x] Add `AI Patch Suggestions` panel to `/bilgeapi-ops`.
- [x] Extend static UI contract test.

## Release Gate & Verification
- [x] Update release gate module/endpoint checks.
- [x] Run target Faz 29 tests.
- [x] Run BilgeAPI unit/integration regression with coverage.
- [x] Export OpenAPI schema.
- [x] Run frontend production build.
- [x] Run release gate.
