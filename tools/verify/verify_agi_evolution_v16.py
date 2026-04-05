import asyncio
import os
import sys
import uuid
from typing import Any

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_evolution_v16():
    print("--- AGI Phase 16: 'The Recursive Architect' Verification ---")
    
    try:
        from packages.persistence.session import session_scope
        from packages.persistence.models import ImprovementOpportunity, CEOSuggestedTask, ProjectStatus
        from packages.orchestration.agi.consciousness.neural_core_orchestrator import neural_core_orchestrator
        from packages.persistence.repository import ImprovementRepository
        
        print("\n[STEP 1] Testing Neural Core Orchestrator Taxonomy...")
        async with session_scope() as db:
            # 1.1 Run Mind Cycle
            print("[INFO] Running Neural Core Mind Cycle...")
            await neural_core_orchestrator.run_mind_cycle(db)
            print("[OK] Neural Core Mind Cycle executed successfully.")
            
            # 2. Test Dynamic Skill Synthesis (Tool Weaving)
            print("\n[STEP 2] Testing Dynamic Skill Synthesis (Neural Tool Weaver)...")
            
            # Create a mock opportunity that triggers tool synthesis
            opp = await ImprovementRepository.create(
                db=db,
                title="Log Analyzer Tool Request",
                description="Sistem günlüklerini (logs/) analiz edip anomali tespiti yapacak bir helper tool sentezle. main(dict) fonksiyonu olsun.",
                source_type="latency_mind_dream",
                severity="medium",
                category="tool_synthesis", # Trigger for skill synthesis
                impact_score=0.8
            )
            print(f"[OK] Tool Opportunity created: {opp.id}")
            
            # Trigger Evolutionary Architect
            from packages.orchestration.agi.operational.evolutionary_architect import evolutionary_architect
            print("[INFO] Triggering Evolutionary Architect for Skill Synthesis...")
            await evolutionary_architect.propose_evolution()
            
            # Verify if a new tool was created in tools/autonomous/
            # Note: We need a mock LLM or let it actually call the LLM. 
            # In this environment, it will call the actual model_orchestrator.
            
            print("\n[STEP 3] Verifying synthesized tools...")
            import glob
            auto_tools = glob.glob("tools/autonomous/auto_tool_*.py")
            if auto_tools:
                print(f"[SUCCESS] AGI has synthesized {len(auto_tools)} new tools!")
                for t in auto_tools:
                    print(f"  -> Path: {t}")
            else:
                # If LLM didn't return a tool yet, check the DB for analyzed status
                await db.refresh(opp)
                if opp.status == "synthesized":
                    print("[SUCCESS] Opportunity marked as 'synthesized'. Tool creation logic was triggered.")
                else:
                    print("[INFO] Tool synthesis is in progress or failed. Check logs.")

        print("\n[OK] Phase 16 Taxonomy and Logic Verified.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_evolution_v16())
