# Split-Brain Response Strategy — Phase 21

## 1. The Challenge
A "Split-Brain" occurs when a network partition allows two separate clusters of regions to believe they both have authority to modify the same global resource (e.g., Codebase, Security Policy).

## 2. Prevention (Design Time)
### Quorum-Based Authority
- Any autonomous change must be validated against the `MeshStateStore`.
- A region is only authorized to execute a task if it can verify that **51% of known regions** recognize it as the current leader for that workload.
- **Role Lease**: Clusters must hold a sub-second "Heartbeat Lease" in the shared state for their assigned expertise.

### Immutable GitOps Baseline
- For Policy changes, the "Truth" is the Git repository.
- Conflicts are resolved by the timestamp of the commit that reaches the **Primary Region (us-east-1)** first.

## 3. Detection (Runtime)
The system detects a potential split-brain if:
- A region attempts to commit a policy gÃ¼ncellemesi with a lower or conflicting version SHA than the current mesh baseline.
- `MeshRouter` receives two "Routed" signals for the same task with different Target Regions.

## 4. Response Logic (Conflict Resolution)
1. **Losing Region Halt**: The region with the older timestamp or smaller quorum immediately halts all non-critical autonomous tasks.
2. **Conflict Flagging**: Conflicting patches are marked as `QUARANTINED_CONFLICT` in the audit logs.
3. **Manual Arbitration**: If the system cannot resolve between two valid high-quality patches from different regions, it triggers a **Security Gate 1 HITL (Human-in-the-Loop)** alert.

## 5. Evidence of Resolution
- `test_federation_under_partition.py` simulates a partition and verifies that only the primary-majority region successfully completes the task, while the isolated region logs an `AUTHORITY_ERROR`.

---
*Status: IMPLEMENTED | Phase 21 Resilience Standard*
