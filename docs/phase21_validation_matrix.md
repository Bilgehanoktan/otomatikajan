# Phase 21 — Validation Matrix (Chaos & Resilience)

This matrix defines the success criteria for the resilience tests and tracks the current proof status.

| ID | Experiment Name | Chaos Trigger | Success Criteria | Proof File | Status |
|----|-----------------|---------------|------------------|------------|--------|
| CP-01 | Regional Partition | Set `mesh_state` Pulse to NULL (15s+) | Traffic shifts to Standby, Isolated Region -> Advisory Mode | `test_region_partition.py` | [ ] |
| CP-02 | Policy Drift | Manually edit `emergency_policy` without Git | Sync detects drift, flags Quarantine/Sync | `test_drift_under_partition.py` | [ ] |
| CP-03 | State Corruption | Ingest string instead of dict into `mesh_state.json` | Router continues via Local Baseline fallback | `test_state_corruption.py` | [ ] |
| CP-04 | Critical Failover | Simulate 0.1 Health for Primary | Detection < 15s, Reroute < 5s. Total MTTR < 30s | `test_failover_metrics.py` | [ ] |
| CP-05 | Federation Safety | Isolate a cluster in a partitioned region | Arbitration prevents split-brain task completion | `test_federation_chaos.py` | [ ] |
| CP-06 | GitOps Integrity | Reject non-signed policy commit | System reverts to last known-good Git SHA | `vcs_integrity_check.py` | [ ] |

## Target Performance Metrikleri (SLAs)
- **Max Detection Delay**: 15s
- **Max Data Loss (Audit)**: 0 items (via local buffering)
- **Split-Brain Frequency**: 0% (Always quarantined)

---
*Generated: 2026.04.15 — Sovereign AGI Resilience Labs*
