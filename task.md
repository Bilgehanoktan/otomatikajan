# Faz 32B — External Agent Capability Registry & Sandbox — Task List

## Kapanış Kontrolleri

- [x] Confirm latest Faz 32B commit exists.
- [x] Confirm tag `bilgeapi-phase32b-agent-sandbox` points at the latest Faz 32B commit.
- [x] Confirm `AgentCapabilityModel` exists.
- [x] Confirm `AgentRunModel` exists.
- [x] Confirm external agent router exists.
- [x] Confirm capability registry, policy engine, sandbox executor and ledger reporter exist.

## Migration

- [x] Add Alembic migration for `repair_agent_capabilities`.
- [x] Add Alembic migration for `repair_agent_runs`.
- [x] Apply migration to local SQLite fallback DB.
- [x] Verify Alembic current/head.

## Documentation

- [x] Rewrite `implementation_plan.md` as Faz 32B-specific plan.
- [x] Rewrite this `task.md` as Faz 32B-specific checklist.
- [x] Rewrite `walkthrough.md` as Faz 32B closeout report.

## Verification

- [x] Run Faz 32B unit/E2E tests:
  `py -3.13 -m pytest tests/repair/test_agent_registry_sandbox_phase32b.py -v`
- [x] Run workflow API import smoke:
  `py -3.13 -c "import services.workflow_api.main; print('workflow api import ok')"`
- [x] Run migration verification:
  `py -3.13 scripts/verify_bilgeapi_migrations.py`
- [x] Confirm no unrelated file enters the Faz 32B fix commit.

## Git

- [x] Stage only Faz 32B fix files.
- [x] Commit migration and documentation cleanup.
- [ ] Move/update `bilgeapi-phase32b-agent-sandbox` tag to final Faz 32B fix commit.
  - Blocked in this run: `git tag -f bilgeapi-phase32b-agent-sandbox` requires `.git/refs/tags` write access and escalation was rejected by the approval reviewer.
