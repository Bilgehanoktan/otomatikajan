import asyncio
import uuid
import os
from datetime import datetime
from sqlalchemy import select
from libs.db.session import AsyncSessionLocal
from libs.db.models.auth_models import SystemIdentity
from services.auth.jwt_auth import AccessControlService
from services.repair.generation.patch_tournament import PatchTournament
from services.repair.generation.candidate_generator import RepairCandidate

async def test_sif_04_autonomous_risk():
    print("--- SIF-04: Autonomous Risk & Quarantine Test ---")
    async with AsyncSessionLocal() as db:
        agent_id = uuid.uuid4()
        agent_name = f"Test_Burst_Agent_{uuid.uuid4().hex[:8]}"
        agent = SystemIdentity(
            id=agent_id,
            name=agent_name,
            identity_type="AGENT",
            role="AUTONOMOUS_AGENT",
            is_active=True,
            trust_score=15,
            quarantined_at=datetime.utcnow(),
            risk_reason="Test: Autonomous Response Triggered"
        )
        db.add(agent)
        await db.commit()
        
        allowed, reason = await AccessControlService.is_allowed(
            db, agent_id, "system", "workflow.approve", role="AUTONOMOUS_AGENT"
        )
        
        print(f"Result: Allowed={allowed}, Reason='{reason}'")
        if allowed is False and "QUARANTINED" in reason:
            print("PASS: SIF-04 Autonomous Lockdown Verified.")
        else:
            raise Exception(f"SIF-04 Verification Failed: {reason}")

async def test_pel_sif_03_tournament_transparency():
    print("--- PEL-SIF-03: Tournament Transparency Test ---")
    c1 = RepairCandidate(
        strategy_name="Adaptive_Retry",
        risk_score=0.1,
        estimated_cost=50.0,
        patch_payload={"action": "retry"}
    )
    c2 = RepairCandidate(
        strategy_name="Blind_Restart",
        risk_score=0.8,
        estimated_cost=200.0,
        patch_payload={"action": "restart"}
    )
    
    tournament = PatchTournament(risk_weight=0.3, cost_weight=0.2, verifier_weight=0.5)
    winner, score = await tournament.run_tournament([c1, c2], [], {})
    
    print(f"Winner: {winner.strategy_name}, Score: {score}")
    if hasattr(winner, "score_breakdown"):
        print(f"Winner Breakdown Found.")
        print("PASS: PEL-SIF-03 Score Transparency Verified.")
    else:
        raise Exception("PEL-SIF-03 Verification Failed: score_breakdown missing.")

async def main():
    try:
        await test_sif_04_autonomous_risk()
        await test_pel_sif_03_tournament_transparency()
        print("FINAL SYSTEM AUDIT: ALL SYSTEMS SECURED.")
    except Exception as e:
        print(f"AUDIT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
