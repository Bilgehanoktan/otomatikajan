# Regional Partition Playbook — Phase 21

## 🚩 Scenario: Network Partition
A "Network Partition" occurs when two or more regions are operational but cannot communicate with each other (Split-Brain risk).

### 1. Detection (Automated)
- **Pulse Loss**: `MeshStateStore` detects missing updates from Region X for > 15s.
- **Quorum Loss**: The remaining connected regions check if they represent the **Majority (N/2 + 1)**.
- **Event Logging**: `MeshRouter` logs `EVENT_REGION_PARTITIONED`.

### 2. Immediate Response
#### Region(s) with Quorum:
- Continue processing high-risk tasks.
- Mark the partitioned region as `QUARANTINED` in the shared store.
- Re-route all critical traffic to the remaining healthy regions.

#### Isolated Region(s) (No Quorum):
- **Advisory Mode Activation**: All autonomous write operations are frozen.
- **Fail-Safe Read-Only**: Agents can still provide information but cannot commit changes to the codebase or policies.
- **Local Buffer**: Store audit logs locally until reconnection.

### 3. Manual Intervention (Operator Steps)
If the partition lasts > 5 mins:
1. Check the **Mesh Dashboard** for the "Partition Map."
2. Verify regional cloud health (AWS/GCP status pages).
3. If the isolated region is permanently lost, use `mesh_force_deregister <region_id>` to update the Quorum baseline.

### 4. Reconciliation (Re-integration)
When a partitioned region regains connectivity:
1. **Policy Sync Check**: `PolicySync` immediately runs `check_drift` against the GitOps baseline.
2. **Audit Merge**: Local audit logs from the isolated period are pushed to the global aggregator.
3. **Quorum Restoration**: The global `MeshStateStore` updates the healthy region count.
4. **Gradual Rollback**: Start with read-only traffic for 2 minutes before allowing autonomous writes.

---
*Verified via test_region_partition.py*
