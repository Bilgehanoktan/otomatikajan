# Live Operations Safety Matrix — Phase 18

## Overview
This matrix maps specific incident types to their corresponding autonomous responses, safety gates, and fallback modes.

---

## 🛡️ Safety Response Matrix

| Incident Type | Severity | Autonomous Response | Safety Gate | Fallback Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Logic Regression** | High (P1) | Immediate Rollback | Post-action report | Version N-1 |
| **Token Cost Spike** | Medium (P2) | Throttle / Model Downgrade | Budget Alert | Cheap-Safe Route |
| **Dependency Outage** | High (P1) | Cache-Only Mode / Retry | Isolation Alert | Read-Only |
| **Validation Failure** | Crit (P0) | **Safety Freeze** (System Stop) | Operator Siren | Hard Quarantine |
| **Latency Degradation**| Low (P3) | Resource Scaling | Metric Audit | Normal |
| **Security Breach** | Crit (P0) | Connector Isolation | **Immediate HITL** | Lockdown Mode |

---

## ⚙️ Threshold Settings (Reference)

### A. Automatic Rollback (Canary)
- **Threshold:** Error Rate > 2% increase in 5 mins.
- **Latency:** Post-rollout verification takes 15 mins.
- **Trigger:** Auto-revert to stable git hash.

### B. Autonomy Downgrade (Safety Freeze)
- **Trigger:** $>3$ consecutive failed self-correction attempts.
- **Result:** System enters **"L1 forced HITL"**. Changes are suggestion-only.

### C. Resource Throttling
- **Trigger:** Cloud Run cost projection > $200/day.
- **Action:** Scale down minimum instances to 0, increase concurrency limit.

---

## 🚒 Emergency Fallback Modes

1.  **Read-Only Mode:** System continues to answer queries but disables all `INSERT/UPDATE` operations except logs.
2.  **Connector Isolation:** Disables external tool execution (e.g., stopping a rogue agent from making API calls).
3.  **Model Downgrade:** Switches from `gpt-4o` to `gpt-4o-mini` or local `llama3` to save costs and reduce complexity during high-traffic incidents.

---

> [!IMPORTANT]
> This matrix is a living document. It is calibrated weekly using evidence from the **False Positive / False Negative** reports generated in Phase 17.
