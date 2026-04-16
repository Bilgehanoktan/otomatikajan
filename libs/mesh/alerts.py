"""
Sovereign AGI - Canonical Alert & Incident Dictionary
This file defines the standard nomenclature used by the Backend, UI, and Operations Runbooks.
DO NOT modify these keys without updating the corresponding documentation.
"""

from enum import Enum

class AlertCode(str, Enum):
    # --- MESH & QUORUM ---
    ERR_QUORUM_LOST = "ERR_QUORUM_LOST" # System is partitioned, consensus lost.
    MESH_PARTITION_DETECTED = "MESH_PARTITION_DETECTED" # Split-brain risk detected.
    PULSE_SILENCE = "PULSE_SILENCE" # Heartbeat missing from a region.

    # --- FAILOVER & ROLES ---
    INCIDENT_REGIONAL_FAILOVER = "INCIDENT_REGIONAL_FAILOVER" # Failover process initiated.
    FAILOVER_COMPLETE = "FAILOVER_COMPLETE" # New primary promoted.
    MESH_PROMOTION_FAILURE = "MESH_PROMOTION_FAILURE" # Regional promotion failed.

    # --- PERFORMANCE & LOAD ---
    LATENCY_THRESHOLD_EXCEEDED = "LATENCY_THRESHOLD_EXCEEDED" # Cross-region latency > 1000ms.
    LOAD_CRITICAL_SPIKE = "LOAD_CRITICAL_SPIKE" # Predictive load > 90% capacity.

    # --- FINANCIAL & BUDGET ---
    ALERT_COST_SPIKE = "ALERT_COST_SPIKE" # Burn rate > $10/min.
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED" # Tier-based quota limit reached.

    # --- EMERGENCY ---
    EMERGENCY_FREEZE_ACTIVE = "EMERGENCY_FREEZE_ACTIVE" # Advisory mode (read-only) enforced.
    SAFETY_BLOCK_TRIGGERED = "SAFETY_BLOCK_TRIGGERED" # Autonomous healing blocked by Safety Gate.

# Mapping to Human Readable Messages
ALERT_METADATA = {
    AlertCode.ERR_QUORUM_LOST: {
        "severity": "CRITICAL",
        "description": "Majority of nodes are unreachable. Adopting Advisory Mode.",
        "runbook_ref": "docs/global_failover_runbook.md#quorum-recovery"
    },
    AlertCode.INCIDENT_REGIONAL_FAILOVER: {
        "severity": "WARNING",
        "description": "Region health degraded. Migration to standby in progress.",
        "runbook_ref": "docs/global_failover_runbook.md#failover-process"
    },
    AlertCode.ALERT_COST_SPIKE: {
        "severity": "CRITICAL",
        "description": "Anomalous financial burn detected. Fleet scaling restricted.",
        "runbook_ref": "docs/ops_runbook.md#financial-governance"
    }
}
