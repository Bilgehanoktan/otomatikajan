import asyncio
import os
import sys
import uuid
from typing import Any

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_self_evolution():
    print("--- AGI Phase 15 Self-Evolution Verification ---")
    
    try:
        from packages.persistence.session import session_scope
        from packages.persistence.models import ImprovementOpportunity, CEOSuggestedTask, ProjectStatus
        from packages.orchestration.agi.consciousness.neural_core_orchestrator import neural_core_orchestrator
        from packages.persistence.repository import ImprovementRepository
        
        print("[STEP 1] Creating a simulated Improvement Opportunity...")
        async with session_scope() as db:
            # Delete old ones to ensure our mock is picked up
            from sqlalchemy import delete
            await db.execute(delete(ImprovementOpportunity))
            
            # Create a mock opportunity for Evolutionary Architect to pick up
            opp = await ImprovementRepository.create(
                db=db,
                title="Gecikmeli Zihin Bellek Sızıntısı Analizi",
                description="core/agi/cognitive/latency_mind_processor.py dosyasındaki _dream_task fonksiyonunda sonsuz döngü riski saptandı.",
                source_type="latency_mind_dream",
                severity="high",
                category="reliability",
                impact_score=1.0
            )
            print(f"[OK] Opportunity created: {opp.id}")
            
            # 2. Run Mind Cycle
            print("[STEP 2] Running Neural Core Mind Cycle (triggers Evolutionary Architect)...")
            await neural_core_orchestrator.run_mind_cycle(db)
            
            # 3. Verify CEO Suggestion
            print("[STEP 3] Verifying CEO Suggested Tasks for Evolution patches...")
            from sqlalchemy import select
            result = await db.execute(
                select(CEOSuggestedTask).where(CEOSuggestedTask.opportunity_id == opp.id)
            )
            suggestion = result.scalar_one_or_none()
            
            if suggestion:
                print(f"[SUCCESS] AGI has proposed a code evolution patch!")
                print(f"  -> Title: {suggestion.title}")
                print(f"  -> Suggestion Preview: {suggestion.description[:100]}...")
            else:
                print("[FAILED] No evolution suggestion was found in the DB.")
                
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_self_evolution())
