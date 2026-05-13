# Skill Integration Plan

## Scope

Integrate useful skills from the archived `everything-claude-code` source into the active project skill catalog.

## Selected Skills

- `e2e-testing`: Adds Playwright E2E patterns that complement the existing TDD and frontend skills.
- `eval-harness`: Adds eval-driven development guidance for agent reliability and regression checks.
- `nextjs-turbopack`: Adds Next.js/Turbopack operational guidance for frontend development.

## Deferred Skills

- `everything-claude-code`: Deferred because it contains conventions for a different repository and could conflict with this project's governance.
- Other content/marketing/API-provider-specific skills: Deferred until a concrete project need exists.

## Steps

1. Copy the selected skill directories into `.agents/skills/`.
2. Normalize skill metadata and remove Claude-specific command assumptions where needed.
3. Update `AGENTS.md` so the active skill catalog reflects the new capabilities.
4. Verify that the selected skill directories and `SKILL.md` entrypoints exist.

---

# Self-Healing Runtime Guard v1 Implementation Plan

## Scope

Add runtime diagnostics and safe repair visibility for config, database fallback, queue, Redis, API URL, RBAC role and workflow-store drift. The system reports actionable causes instead of a generic `DEGRADED` state and only performs low-risk runtime repairs.

## Steps

1. Add `RuntimeDiagnosticsService` with deterministic diagnostic rules and unit coverage.
2. Expose `/api/v1/health/runtime-diagnostics` and RBAC-protected `/api/v1/health/runtime-diagnostics/{id}/repair`.
3. Enforce startup self-check logging for full-stack profile mismatches without mutating secrets, roles, Docker or migrations.
4. Surface diagnostics in `ResourceHeader`, `/system-health`, and workflow create/approve 403 messages.
5. Verify backend import, targeted backend tests and frontend production build.

---

# Egemen YAZ Self-Repair Phase 1-3 Implementation Plan

## Scope

Add a safe, report-only self-repair skeleton that converts a failed test or trace payload into a repair case, localizes suspected files, prepares a patch candidate, verifies it in a sandbox copy, runs verifier and risk adapters, and writes JSON output artifacts.

## Safety Boundaries

- Do not merge, commit, or patch `main` / production directly.
- Apply candidate patches only in a temporary sandbox copy.
- Block autonomous repair for forbidden or high-risk paths.
- Produce `repair_outputs/{incident_id}/` artifacts for operator review.

## Steps

1. Add repair dataclasses and case/evidence builders.
2. Add a deterministic code localizer with traceback, failed-test, log, allowed-path, and recent-file scoring.
3. Add a mock-ready patch candidate runner with a prompt template and future agent integration TODO.
4. Add sandbox execution using Docker when explicitly available, with local temp-copy fallback.
5. Add verifier and risk adapter connection points.
6. Add report writer and CLI-driven orchestrator flow.
7. Cover the flow with targeted `tests/repair` unit tests.
