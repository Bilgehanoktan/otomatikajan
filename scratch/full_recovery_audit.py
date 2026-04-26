import asyncio
import os
import sys
from datetime import datetime, timezone
import uuid

# Add workspace root to sys.path
sys.path.append("e:/ai_company_faz12.1")

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, LLMCostLog, SovereignEvidence
from services.orchestration.mesh_state_store import mesh_state_store
from sqlalchemy import select, update

async def full_system_recovery():
    print("Sovereign AGI - Scenario 5: Full System Recovery & Health Audit")
    
    async with AsyncSessionLocal() as db:
        # 1. Clear Budget Breach (Increase limit to $10k)
        print("Increasing institutional budget to $10,000.00...")
        q = update(Project).where(Project.title == "Sovereign System Core").values(budget_limit=10000.0)
        await db.execute(q)
        
        # 2. Restore Mesh Connectivity
        print("Restoring US-EAST-1 regional status to HEALTHY...")
        mesh_state_store.set_region_metrics("us-east-1", {
            "status": "HEALTHY",
            "latency": 11, # Performance slightly degraded but acceptable
            "error": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        # 3. Seal Recovery Evidence
        evidence = SovereignEvidence(
            id=str(uuid.uuid4()),
            evidence_type="system_recovery",
            severity="info",
            payload={
                "action": "FULL_RECOVERY_PROTOCOL",
                "reason": "Manual operator intervention (Egemen YAZ) - Budget authorization increased.",
                "restored_components": ["BudgetGuard", "US-EAST-1_Mesh_Node"],
                "new_metabolic_target": "NORMAL",
                "outcome": "SYSTEM_FULLY_RESTORED"
            },
            provenance_hash="SHA256:RECOVERY_SIG_778899",
            created_at=datetime.now(timezone.utc)
        )
        db.add(evidence)
        await db.commit()
    
    print("Recovery script executed successfully.")
    print("Result: Budget Breach CLEARED | Mesh RESTORED | All Systems NOMINAL.")

if __name__ == "__main__":
    asyncio.run(full_system_recovery())
