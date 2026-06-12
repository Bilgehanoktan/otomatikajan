# BilgeAPI v1.2.0 Release Notes

We are excited to announce the release of **BilgeAPI v1.2.0**. This release completes **Phase 31 (Sovereign Governor, Watchdog & Self-Healing)** and **Phase 32 (External Agent Sandbox & Governance)**. It brings robust capability registry mechanisms, isolated sandbox runtimes, strict output verifiers, and risk-score based simulation policy prevention gates directly onto the platform.

---

## 1. Feature Highlights

### Phase 31: Governor / Watchdog / Self-Healing
- **Live System Watchdog**: Continuous passive intake of health telemetry and automatic runbook alignment.
- **Self-Healing Loop**: Automatic patch orchestration, AST syntax verification, and dry-run execution checks.
- **Sovereign Governor**: Immutable proof chains logging all system modifications using SHA-256 hashes and ledger audits.

### Phase 32: External Agent Sandbox & Governance
- **Agent Capability Registry**: Central registry managing third-party agent permission allowlists (allowed domains, allowed paths, maximum costs). All agents default to `enabled=False` and sandbox `read-only` modes to enforce security by default.
- **Sandbox Executor**: Isolated ephemeral directory copies ignoring heavy platform directories (`.playwright-browsers`, `.nx`, `.agents`) for disk and speed optimization.
- **Output Promotion Gate**: Secure dry-run workspace validations prevent dirtying main git repos. Enforces terminal states (`PROMOTED`, `REJECTED`) and exact multi-stage hash chains matching:
  `artifact_hash == verified_artifact_hash == approved_artifact_hash == promoted_artifact_hash`.
- **Policy Simulation & Operator UI (32D/E)**:
  - Dry-run policy simulator assessing risk score thresholds (0-24 Low, 25-49 Medium, 50-74 High, 75-100 Critical).
  - Hard-gated promotion execution requiring simulation hashes to match the promotion state before integration.
  - Granular console UI for agent management in the Refine Control Plane.

---

## 2. Security Guarantees & Constraints
- **Zero Auto-Merge / Auto-Push**: External agents cannot commit or push code directly to main repos.
- **Read-Only Policy Simulation**: Simulator never mutates database attributes, rules, or files.
- **Path Traversal Guards**: Absolute canonical resolution (`Path.resolve()`) blocks symlink or `../` escapes outside the designated workspace.

---

## 3. Database Migration Notes
- Fully migrated to head migration `3b517c6cb58a` (added `repair_agent_promotions` table). All developer environments must execute:
  ```powershell
  python -m alembic upgrade head
  ```
