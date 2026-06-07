# Faz 27 - Admin UI / Ops Console - Task List

## Planning
- [x] Add Faz 27 scope to `implementation_plan.md`.
- [x] Create this `task.md` checklist.

## Frontend Routing & Proxy
- [x] Add `/bilgeapi/:path*` rewrite in `apps/refine_control_plane/next.config.ts`.
- [x] Create `/bilgeapi-ops` route in `apps/refine_control_plane/src/app/bilgeapi-ops/page.tsx`.
- [x] Register `bilgeapi-ops` resource in `apps/refine_control_plane/src/app/providers.tsx`.
- [x] Add `bilgeapi-ops` to `apps/refine_control_plane/src/components/Sidebar.tsx`.

## BilgeAPI Client Layer
- [x] Create `apps/refine_control_plane/src/lib/bilgeapiOpsClient.ts`.
- [x] Support `X-API-Key` authenticated requests.
- [x] Support API key create/list/revoke/quota usage.
- [x] Support research, proposal, draft PR, verification, feedback and patch revision calls.
- [x] Support release gate and audit event reads.
- [x] Redact plaintext API key in local action logs.

## Ops Console Panels
- [x] Dashboard summary widget set.
- [x] API key management panel.
- [x] Quota monitoring panel.
- [x] Research and proposal panel.
- [x] Draft PR and sandbox verification panel.
- [x] Reviewer feedback and patch revision panel.
- [x] Release gate status widget.
- [x] Audit trail panel.

## Verification
- [x] Add static contract test for Faz 27 UI wiring.
- [x] Run static contract test.
- [x] Run frontend build.
- [x] Verify `/bilgeapi-ops` route over local frontend dev server.
- [x] Run BilgeAPI regression suite.
- [x] Re-export OpenAPI schema.
- [x] Run release gate.
- [x] Verify Docker/live smoke.
- [x] Commit Faz 27 changes without unrelated staged files.
