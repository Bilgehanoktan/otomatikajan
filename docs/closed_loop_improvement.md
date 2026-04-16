# Closed-Loop Self-Improvement Engine

This document describes the autonomous self-healing and optimization cycle of the Sovereign AGI platform.

## The Cycle
1. **Detection:** Telemetry and Operational Incidents are monitored for repetitive failure patterns.
2. **Clustering:** `ProposalEngine` groups incidents into `ImprovementOpportunities`.
3. **Drafting:** CEO / Architect agents draft a `SystemImprovement` patch.
4. **Risk Scoring:** `RiskScoring` service evaluates the patch's risk level (0.0 - 1.0).
5. **Approval:** Low-risk patches are sent to Canary; high-risk patches wait for Human Approval.
6. **Observation:** `CanaryWatcher` worker monitors the system for 15 minutes. If a related incident appears, it triggers an immediate Git rollback.
7. **Promotion:** If the window closes without negative markers, the patch is promoted to 'applied'.


## Key Services & Components
- `services/improve/proposal_engine.py`: Evidence clustering and patch generation.
- `services/improve/risk_scoring.py`: Security & impact analysis.
- `services/improve/rollout_manager.py`: Git-based snapshotting and safe rollout.
- `workers/improvement_worker/canary_watcher.py`: Verification and promotion loop.
