# Global Failover Runbook — Phase 21

## 1. Overview
This runbook describes the process for moving the **Global Sovereign Center of Gravity** between regions during a persistent Level 2 (Critical) or Level 3 (Isolated) failure.

## 2. Failover Trigger Conditions
Failover is triggered and logged as `INCIDENT_REGIONAL_FAILOVER` if:
- **Region Health** remains < 0.2 for more than 45 seconds.
- **Latency Matrix** (Alert: `LATENCY_THRESHOLD_EXCEEDED`) shows > 1000ms from all other mesh nodes to the current Primary.
- **Heartbeat Silence** (Alert: `PULSE_SILENCE`): No state updates (Pulse) for > 30 seconds.
- **Quorum Loss** (Alert: `ERR_QUORUM_LOST`): Majority of nodes are unreachable.

## 3. Automated Failover Process
### Step 1: Drain Primary (us-east-1)
- Router shuts down incoming external requests to us-east-1.
- Active agent tasks are checkpointed or quarantined.

### Step 2: Promote Standby (eu-central-1)
- `MeshRouter` promotes EU-CENTRAL-1 to the **Primary Management Role**.
- `PolicySync` forces a Git baseline pull to the new primary.
- `MeshStateStore` updates the `ROLE_OWNER` key.

### Step 3: Global Persistence Update
- Mesh DNS/Router entries update to point to EU.
- Latency Adapter starts measuring from the EU baseline.

## 4. Manual Failback Procedures (Return to US)
Only perform failback after the Primary region has been stable (nominal) for **> 15 minutes**.

1. **Verify State**: Ensure EU and US states are 100% synchronized via `PolicySync.check_drift`.
2. **Execute Swap**: Run `mesh_trigger_promotion us-east-1`.
3. **Monitor**: Watch the **Mesh Dashboard** for 5 minutes. If latency jitter occurs, trigger immediate rollback to EU.

## 5. Emergency "Kill Switch"
If the whole mesh becomes unstable due to a cascading routing loop:
1. Run `mesh_emergency_freeze --all` (Logs: `EMERGENCY_FREEZE_ACTIVE`).
2. All regions enter **Safe-Mode (Local Proxy Only)**.
3. Manual intervention is required to restart the global mesh.

---
*Operational Evidence: test_cross_region_failover.py*
