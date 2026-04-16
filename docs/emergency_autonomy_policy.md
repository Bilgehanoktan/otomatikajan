# Emergency Autonomy Policy — Sovereign AGI

## Overview
This policy defines the autonomous decision-making power of the Sovereign AGI platform during high-severity (P0/P1) incidents. It ensures that stability always supersedes autonomous change.

---

## 🏗️ 1. Autonomy Levels
The system operates in one of three autonomy states based on current health metrics:

| Level | State | Autonomous Action | HITL Requirement |
| :--- | :--- | :--- | :--- |
| **Normal** | Balanced | Patching, minor improvements allowed. | Low (Standard audit) |
| **Degraded** | Guarded | Rollbacks prioritized, patches require approval. | High (All changes blocked) |
| **Emergency** | Restricted | **Self-Correction Freeze.** Only rollbacks allowed. | Mandatory (Hard Override) |

---

## ⚠️ 2. Automatic Rollback Triggers
The system **must** autonomously trigger a rollback if any of the following occur after a patch rollout:

1.  **Canary Failure:** Error rate in canary group increases by **>5%** compared to baseline.
2.  **Health Breach:** System health score drops below **70/100**.
3.  **Budget Breach:** Operational costs (tokens/infra) spike by **>200%** in < 15 minutes.
4.  **MTTR Lag:** A detected incident is not resolved within the defined **Time-to-Resolution** threshold.

---

## 🛑 3. Hard Safety Zones (No-Autonomy Zones)
The system is **FORBIDDEN** from performing autonomous actions in these areas without explicit human approval:

*   **Financial Access:** Adjusting billing limits or external payment connectors.
*   **Security Policy:** Modifying RBAC roles, permission sets, or encryption keys.
*   **Destructive Data Ops:** Permanent deletion of historical logs or user databases.
*   **Governance Bypass:** Disabling audit trails or logging middleware.

---

## 🔄 4. Evidence-Backed Escalation
Every autonomous emergency action must be justified by evidence:
- **Trigger:** Metric value + Timestamp.
- **Evidence:** SigNoz TraceID + Log snippet.
- **Action:** Rollback version + Affected components.
- **Result:** Delta in health score post-action.

---

> [!CAUTION]
> If the Risk Scoring engine cannot determine a clear path forward with >90% confidence during an emergency, it **must** immediately transition to **L1 forced HITL (Human-in-the-loop)** and sound the operator sirens.
