# Operational Runbook: Sovereign AGI

This document defines the standard procedures for managing Sovereign AGI in production.

## 1. Decision Matrix for Manual Intervention

| Action | When to use | Rule of Thumb |
| :--- | :--- | :--- |
| **Cancel** | Runaway cost, critical bug identified, user request change. | Kill immediately if cost > $10 in 1 min. |
| **Retry** | Transient network errors, rate limits (429), DB lock timeout. | Max 3 retries per step. |
| **Replay** | Logic fix applied, partial failure where context is still valid. | Use when state is clear but execution failed. |
| **Approve** | L1/L2 approval requests, budget threshold exceeded. | Architect review for code, Operator review for cost. |
| **Override** | Deadlock, incorrect model decision, state correction. | Document reason in Audit Trail manually. |

## 2. Emergency Shutdown

If the system exhibits aggressive behavior or unexplained resource consumption:
1. Set `SOVEREIGN_MODE=safe` in `.env`.
2. Restart services: `docker-compose restart`.
3. Self-heal will be disabled, system becomes read-only.

## 3. Maintenance Windows
Standard maintenance should be performed between 02:00 - 04:00 UTC.
Inform Telegram users via `/broadcast` command before starting.
