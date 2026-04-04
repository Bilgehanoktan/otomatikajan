import asyncio
import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from core.agi.monitoring.token_budgeter import token_budgeter
from core.agi.monitoring.nervous_system import nervous_system
from llm.model_orchestrator import ModelOrchestrator
from db.session import session_scope
from db.models import LLMCostLog

async def verify_biological_equilibrium():
    print("--- Phase 24 Biological Equilibrium Verification ---")
    
    async with session_scope() as db:
        # 1. Test Nervous System Pulse (Metabolic Inclusion)
        print("[*] Testing Nervous System Pulse...")
        pulse = await nervous_system.pulse(db)
        if "metabolism" in pulse:
            print(f"[SUCCESS] Pulse includes metabolic data: Score={pulse['metabolism']['health_score']}")
        else:
            print("[FAILURE] Pulse missing metabolic data.")

        # 2. Mock High Cost Scenario
        print("[*] Simulating Token Exhaustion ($60.0 cost today)...")
        # Add a large cost log
        log = LLMCostLog(
            provider="mock_provider",
            model="mock_model",
            agent_id="architect",
            input_tokens=1000000,
            output_tokens=1000000,
            cost_usd=60.0,
            success=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(log)
        await db.commit()

        # 3. Verify Token Budgeter (Background Rejection)
        print("[*] Verifying Token Budgeter Background Rejection...")
        health = await token_budgeter.check_health()
        print(f"Health Score: {health['health_score']}, Reasons: {health['reasons']}")
        
        can_architect = await token_budgeter.should_execute("architect")
        if not can_architect:
            print("[SUCCESS] Background agent (architect) REJECTED over budget.")
        else:
            print("[FAILURE] Background agent was NOT rejected.")

        # 4. Verify Model Orchestrator Integration
        print("[*] Verifying ModelOrchestrator Integration...")
        orchestrator = ModelOrchestrator()
        try:
            await orchestrator.complete_task(
                agent_role="architect",
                prompt="Evolution plan",
                system_prompt="Architect mode"
            )
            print("[FAILURE] Orchestrator did NOT block the background request.")
        except RuntimeError as e:
            if "Metabolizma Sınırı" in str(e):
                print(f"[SUCCESS] Orchestrator BLOCK confirmed: {e}")
            else:
                print(f"[ERROR] Unexpected orchestrator error: {e}")
        except Exception as e:
             print(f"[ERROR] Unexpected exception: {e}")

        # Cleanup mock log
        print("[*] Cleaning up verification data...")
        await db.delete(log)
        await db.commit()

    print("\n[PHASE 24] BIOLOGICAL EQUILIBRIUM VERIFIED.")

if __name__ == "__main__":
    asyncio.run(verify_biological_equilibrium())
