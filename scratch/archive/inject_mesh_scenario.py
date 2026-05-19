import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
import uuid

# Add workspace root to sys.path
sys.path.append("e:/ai_company_faz12.1")

from services.orchestration.mesh_state_store import mesh_state_store
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SovereignEvidence

async def inject_mesh_scenario():
    print("Sovereign AGI - Scenario 4: Federated Mesh Orchestration")
    
    # 1. Setup Initial Mesh State
    regions = {
        "us-east-1": {"name": "North Virginia (Master)", "latency": 9, "status": "HEALTHY", "load": 0.45},
        "eu-central-1": {"name": "Frankfurt (Standby)", "latency": 42, "status": "HEALTHY", "load": 0.12},
        "ap-southeast-1": {"name": "Singapore", "latency": 115, "status": "HEALTHY", "load": 0.08}
    }
    
    for rid, metrics in regions.items():
        mesh_state_store.set_region_metrics(rid, metrics)
    
    print("Initial mesh state initialized.")
    await asyncio.sleep(1)
    
    # 2. Trigger Regional Failure (Simulation)
    print("Simulating regional outage in us-east-1...")
    mesh_state_store.set_region_metrics("us-east-1", {
        "status": "OFFLINE",
        "latency": 9999,
        "error": "Backbone Disruption",
        "updated_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    })
    
    # 3. Trigger Autonomous Failover Redirection
    async with AsyncSessionLocal() as db:
        evidence = SovereignEvidence(
            id=str(uuid.uuid4()),
            evidence_type="mesh_failover",
            severity="warning",
            payload={
                "component_name": "FederatedMeshController",
                "rationale": "US-EAST-1 regional outage detected (Heartbeat timeout > 15s). Otonom redirection to EU-CENTRAL-1 (Best Latency Standby) initiated to preserve service continuity.",
                "trigger_event": "MESH_REGION_TIMEOUT",
                "outcome": "REDIRECITON_SUCCESSFUL",
                "confidence_score": 1.0,
                "failover_target": "eu-central-1"
            },
            provenance_hash="SHA256:MESH_SECURE_FAILOVER_7712",
            created_at=datetime.now(timezone.utc)
        )
        db.add(evidence)
        await db.commit()
    
    print("Scenario 4: Federated Mesh Failover Injected Successfully.")
    print("Result: us-east-1 OFFLINE | Redirection to eu-central-1 SEALED.")

if __name__ == "__main__":
    asyncio.run(inject_mesh_scenario())
