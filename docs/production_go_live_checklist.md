# Production Go-Live Checklist (Phase 14 Sprint 1)

This checklist defines the critical gates that must be passed before the Sovereign AGI system is declared "Go-Live Ready".

## 1. Environment & Infrastructure
- [ ] **Env-Lock:** Verify all production environment variables are locked and consistent with `libs/config.py`.
- [ ] **Secrets Management:** Ensure sensitive keys (LLM API keys, DB credentials) are stored securely and not in plaintext configs.
- [ ] **Resource Monitoring:** Confirm SigNoz/OpenTelemetry spans are flowing for the `CentralExecutive` and `WorkflowRunner`.

## 2. Data & Persistence
- [ ] **Alembic Migrations:** Run `verify_db_schema.py` to ensure the current database schema matches the `core_models.py`.
- [ ] **Backup Verification:** Execute `backup_db.bat` and verify that the resulting `.sql`/`.bak` file is valid.
- [ ] **Restore Protocol:** Perform a dry-run restoration using `restore_db.bat` on a staging instance.

## 3. Security & Governance
- [ ] **Autonomy Lockdown:** Set `current_global_level: L1` in `configs/autonomy_policy.yaml` for the initial launch.
- [ ] **Audit Gate:** Verify that all tool calls are being logged to the `audit_logs` table with non-repudiable timestamps.
- [ ] **RBAC Verification:** Ensure only 'Admin' and 'Operator' roles can access critical control endpoints.

## 4. Operational Readiness (Smoke Tests)
- [ ] **End-to-End Workflow:** Run a test workflow (e.g., "System Health Check") and verify completion.
- [ ] **Manual Intervention:** Test the `Approve` button in the Control Plane to ensure it unblocks a waiting step.
- [ ] **Emergency Stop:** Trigger a system-wide cancel and verify all active workers terminate gracefully.

---
> [!IMPORTANT]
> Failure to pass even a single "P0" marked item (Env, Migration, Audit) blocks the production release.
