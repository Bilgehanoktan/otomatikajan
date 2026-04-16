# Emergency Rollback Protocol — Phase 18

## 1. Overview
The **Emergency Rollback Protocol (ERP)** is the ultimate failsafe. It describes the automated and manual steps to return the Sovereign AGI platform to a "Known Good State" when critical failures occur.

---

## 2. The Golden Rule
> "A partial fix during an incident is worse than a full rollback to a stable state." 
> — Sovereign AGI Safety Directive

---

## 3. Rollback Levels

### Level A: Workflow State Rollback
*   **Scope:** Single workflow instance failure.
*   **Action:** Revert `Project` and `WorkflowStep` states to the last successful checkpoint.
*   **Method:** Durable Execution Replay (Phase 13.04).
*   **Trigger:** AI Diagnosis identifies a fatal logic error.

### Level B: Service-Level Rollback (Canary)
*   **Scope:** Entire service (e.g., `workflow-api`) deployment failure.
*   **Action:** Switch traffic back to the previous stable container image.
*   **Method:** Cloud Run Revision Revert / GitHub Actions Rollback.
*   **Trigger:** Phase 17 metrics detect global error rate increase > 5%.

### Level C: Infrastructure Isolation (Emergency Stop)
*   **Scope:** Global platform instability or runaway autonomy.
*   **Action:** **Kill Switch**. Terminate all active workers and set DB to Read-Only.
*   **Method:** `docker-compose down` (Local) / GKE Node Scale 0 (Cloud).
*   **Trigger:** Operator Manual Trigger or Safety Matrix P0 Breach.

---

## 4. Automated Rollback Chain (SOP)
1.  **Detection:** Metric (e.g., OTel latency) hits **Trigger Threshold**.
2.  **Notification:** PagerDuty / Slack / Dashboard Siren triggered.
3.  **Autonomous Decision:** Policy Engine validates the incident against the **Safety Matrix**.
4.  **Action Execution:**
    - If `Level A`: Execute compensation actions and replay from N-1.
    - If `Level B`: Trigger GitHub Action `rollout-revert.yml`.
5.  **Verification:** System health re-evaluated 5 minutes post-action.
6.  **Evidence Lock:** TraceID and logs archived for **Incident Post-Mortem**.

---

## 5. Recovery Verification
A rollback is considered successful ONLY if:
- System Health Score returns to **>90**.
- Incident metrics (Error Rate, Latency) stabilize.
- **Self-Correction Freeze** is lifted manually by an authorized **OPERATOR**.

---

> [!CAUTION]
> During a Level C Rollback (Isolation), no autonomous recovery is allowed. A human **MANAGER** must manually re-verify the platform state before resuming operations.
