# Operational Runbook (Phase 14 Sprint 2)

This document provides step-by-step procedures for the ongoing maintenance and incident response of the Sovereign AGI platform.

## 1. Incident Response Matrix
| Scenario | Detection Method | Action | Tool / Script |
|----------|------------------|--------|---------------|
| Database Corruption | Workflow Failures / Error Logs | Trigger DB Restore | `scripts/production/restore_db.bat` |
| Stuck Workflow | "In Progress" status > 2 hours | Replay Step | Control Plane UI (Replay button) |
| High Operational Drift | Observability Dashboard Alert | Lockdown System | `configs/autonomy_policy.yaml` (Set L1) |
| Worker Crash | Heartbeat alert in SigNoz | Restart Worker Pods | `kubectl rollout restart deployment/workers` |

## 2. Data Recovery Procedures

### 2.1 Database Restore
In case of critical data loss or corruption:
1. Stop all active background workers.
2. Navigate to `scripts/production/`.
3. Execute `restore_db.bat`.
4. Run `verify_db_schema.py` to ensure consistency.
5. Restart workers and verify system health.

### 2.2 Manual Override Protocol
When an agent decision is flagged for high-risk:
1. Review the logic trace in the "Refine Control Plane" -> Approvals tab.
2. If the logic is sound but risk is high, use "Approve".
3. If the decision is incorrect, use "Manual Override" to provide a corrected context/input.
4. Document the override reason in the provided form for audit purposes.

## 3. System Hardening (Autonomy Control)
The system supports L1 (Manual) to L4 (Sovereign) autonomy levels.
- **Emergency Lockdown:** Change `current_global_level` to `L1` in `autonomy_policy.yaml`.
- **Canary Policy:** Use `L2` for non-critical patches during Sprint 4 testing.

---
> [!TIP]
> Always check the `Audit` tab before performing a manual override to understand the preceding agent reasoning.
