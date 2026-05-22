# Autonomous System Audit & Suggestion vs. Self-Repair Mode — System Architecture

## 1. Executive Summary

This architecture defines the separation of responsibilities between **Autonomous System Audit & Suggestion Mode (Audit Mode)** and **Self-Repair Mode**. Both modes operate alongside the existing `self_repair_v1` pipeline. The key objective is to provide comprehensive, read-only system evaluation (Audit Mode) and safe, approved code resolution (Self-Repair Mode) under strict human-in-the-loop governance.

---

## 2. Pipeline Branching & Boundaries

The unified workflow bifurcates based on the selected execution mode:

```
                  [ Trigger: Incident, Failed Test, or Cron ]
                                      │
                                      ▼
                        ┌──────────────────────────┐
                        │  Collect Context & Run   │
                        │   Diagnostic Profiler    │
                        └─────────────┬────────────┘
                                      │
                     Is Mode == Audit or Self-Repair?
                                      │
                     ├────────────────┴────────────────┐
                     ▼                                 ▼
               [ Audit Mode ]                 [ Self-Repair Mode ]
                     │                                 │
         (Strictly Read-Only)                (Approved Code Patching)
                     │                                 │
     ┌───────────────┴───────────────┐        ┌────────┴───────────────┐
     │ Analyze Architecture, Code,   │        │ Run SWE-agent/Mini    │
     │ Test Failures, Security Logs  │        │ Coder Loop in Sandbox  │
     └───────────────┬───────────────┘        └────────┬───────────────┘
                     │                                 │
     ┌───────────────┴───────────────┐        ┌────────┴───────────────┐
     │ Run Verifier Mesh & Diagnostics│        │ Run Verifier Mesh &    │
     │ (Stagehand DOM / Playwright)   │        │ Stagehand Assertions   │
     └───────────────┬───────────────┘        └────────┬───────────────┘
                     │                                 │
     ┌───────────────┴───────────────┐        ┌────────┴───────────────┐
     │ Generate Audit Recommendation │        │ Run Patch Tournament   │
     │ Report (No Code Modified)     │        │ & Risk Assessment Loop │
     └───────────────┬───────────────┘        └────────┬───────────────┘
                     │                                 │
                     ▼                                 ▼
         [ Suggestion Log Created ]             [ Approval Gate ]
                     │                                 │
                     │                          User Approves?
                     │                       ┌─────────┴─────────┐
                     │                       ▼                   ▼
                     │                   [ YES ]               [ NO ]
                     │                       │                   │
                     ▼                       ▼                   ▼
            (Prompt User to Approve   [ Deploy Patch /    [ Cancel Run /
              Self-Repair Run)         Git PR Rollout ]    Discard Patch]
```

---

## 3. Mode Deep Dive

### 3.1. Autonomous System Audit & Suggestion Mode (Audit Mode)
* **Principle**: **Strictly Read-Only**. Zero modifications allowed to source code, configs, or environments.
* **Trigger Loop**: Runs continuously on a cron schedule, manual prompt request, or instantly when a webhook reports an incident/test failure.
* **Workflow Steps**:
  1. **Diagnostics**: Scans the workspace, execution logs, and database models.
  2. **UI Assertion Audits**: Invokes `browserbase/stagehand` backend and python integrations to analyze visual and DOM integrity on live routes.
  3. **Cognitive Integrity Checks**: Evaluates architectural alignment against system guidelines (`AGENTS.md`).
  4. **Reporting**: Automatically outputs a rich suggestion report to the user at:
     `docs/reports/system_audit_suggestion_<timestamp>.md`
  5. **Actionable Suggestions**: The report includes an overview of the issue, root-cause localization, risk analysis, and a structured command to launch Self-Repair:
     `"To automatically fix this issue, run: /repair --id <suggested-case-id>"`

### 3.2. Self-Repair Mode
* **Principle**: **Verification-Driven Correction**. Patch candidates are generated in isolation and only merged/deployed after passing the Verifier Mesh and getting explicit human sign-off.
* **Trigger Loop**: Triggered manually by clicking the auto-generated repair command, approving a plan, or automatically for low-risk incidents (under strict risk-score thresholds).
* **Workflow Steps**:
  1. **Sandbox Patch Generation**: Bootstraps an isolated workspace branch, applying `swe-agent` aci command concepts and `aider` tools to generate patch candidates.
  2. **Tournament Selection**: Runs multiple patch candidates through local test suites and scores them by safety, size, and efficiency.
  3. **Visual & Telemetry Check**: Boots the app on a temporary dynamic port and runs Stagehand tests to ensure zero visual regressions.
  4. **Approval Gate & Rollout**: If the risk score is low, drafts a PR (handled via `pr-agent` review wrapper). If the risk score is high, halts for human gate decision.

---

## 4. Safety & Governance Gates

To prevent rogue agents from compromising the codebase, the following safety constraints are programmatically enforced:

> [!CAUTION]
> * **Audit Mode Code Protection**: The execution runtime of Audit Mode explicitly mocks or disables standard file writing tools (`write_to_file`, `replace_file_content`, `run_command` with write arguments). If a tool attempt is detected, the audit run instantly halts and alerts the human operator.
> * **Risk scoring (PR Gate)**:
>   - Risk score `> 0.30`: Direct patch rollout is blocked. A Git PR is generated, and `pr-agent` reviews it, appending suggestions.
>   - Risk score `<= 0.30`: Eligible for direct patching, but still requires the Verifier Mesh to pass `100%` of test assertions.
