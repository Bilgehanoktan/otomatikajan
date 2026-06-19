# Changelog — BilgeAPI v1.2.0

All notable changes to this project will be documented in this file.

---

## [1.2.0] — 2026-06-12

### Phase 32 — External Agent Governance, Sandbox & Simulation
- **Agent Capability Registry**: Implemented `AgentCapabilityModel` and registry table tracking allowed directories, cost limits, and network permissions. Default state is disabled (`enabled=False`, sandbox `read-only`, `requires_human_approval=True`) for all default seeded agents.
- **Isolated Sandbox Executor**: Subprocess-based run coordinator utilizing copy-on-write temp workspaces, ignoring heavy caching directories (`.playwright-browsers`, `.nx`, `.agents`) to optimize performance and disk footprint.
- **Output Promotion Gate**: Enforced multi-stage hash validation preventing direct branch mutation. Promotion request integration dry-runs occur in temporary worktrees and package approved artifacts to isolated directories.
- **Policy Simulation & Risk Scoring**: Read-only simulator computing risk score thresholds (0-24: LOW/ALLOW, 25-49: MEDIUM/ALLOW, 50-74: HIGH/HUMAN_GATE_REQUIRED, 75-100: CRITICAL/BLOCK). Gated execution strictly checks simulation hashes before apply.
- **Operator UI Console**: Added an "Agents" management tab to the Refine Control Plane dashboard displaying Capability Registry state, execution logs, and promotion detail panels with disabled action safety indicators.

---

## [1.1.0] — 2026-05-24

### Phase 31 — Sovereign Governor, Watchdog & Self-Healing
- **Live Watchdog**: Developed system monitoring hooks evaluating active platform errors and runbook matches.
- **Self-Healing Integration**: Automated diagnostic run triggers, AST syntax validations, and dry-run recovery workflows.
- **Proof Chain Ledger**: Implemented immutable SHA-256 parent-hashed event logging for all operational status updates.
- **Platform Webhook Bridge**: Secure webhook deliverer for dispatching repair requests.
