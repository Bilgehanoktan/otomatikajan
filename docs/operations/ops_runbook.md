# Operational Runbook: Sovereign AGI

This document defines the standard procedures for managing Sovereign AGI in production.

## 1. Decision Matrix for Manual Intervention

| Action | When to use | Rule of Thumb |
| :--- | :--- | :--- |
| **Cancel** | Runaway cost (Alert: `ALERT_COST_SPIKE`), critical bug, user request. | Kill if cost > $10 in 1 min. |
| **Retry** | Transient network errors, rate limits (429). | Max 3 retries per step. |
| **Approve** | L1/L2 requests, budget exhausted (Alert: `BUDGET_EXHAUSTED`). | Architect review. |
| **Override** | Deadlock, incorrect model decision. | Log: `MANUAL_OVERRIDE`. |

## 2. Emergency Shutdown

If the system exhibits aggressive behavior or unexplained resource consumption:
1. Set `SOVEREIGN_MODE=safe` in `.env` (Logs: `EMERGENCY_FREEZE_ACTIVE`).
2. Restart services: `docker-compose restart`.
3. Self-heal disabled, system becomes read-only.

## 3. Maintenance Windows
Standard maintenance should be performed between 02:00 - 04:00 UTC.
Inform Telegram users via `/broadcast` command before starting.
