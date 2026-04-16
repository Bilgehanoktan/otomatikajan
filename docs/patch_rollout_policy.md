# Patch Rollout & Rollback Policy

This document defines the safety standards for applying autonomous patches to the production environment.

## 1. Rollout Strategies
- **Canary:** Apply a patch to 10% of workers or a single non-critical project ID.
- **Verification Gate:** Wait for 15 minutes of operational telemetry. If no `OperationalIncident` is linked to the patch, proceed.
- **Full Rollout:** Gradual deployment across all clusters.

## 2. Automatic Rollback
Rollback is triggered if:
- Error rate increases by > 5% within the canary window.
- A P0/P1 `OperationalIncident` is detected.
- System latency exceeds baseline by > 30%.

## 3. Human Oversight
- Every autonomous patch must be visible in the `Audit` and `Approvals` panels of the Control Plane.
- Operators can trigger an `Emergency Stop` which rolls back all current canary patches and locks the `RolloutManager`.
