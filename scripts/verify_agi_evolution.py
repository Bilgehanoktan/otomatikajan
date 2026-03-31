import asyncio
import os
import sys

sys.path.append(os.getcwd())

async def verify_agi_evolution():
    print("--- AGI Phase 13 Action Genesis Verification ---")
    
    try:
        from core.agi.consciousness.neural_core_orchestrator import NeuralCoreOrchestrator
        from db.session import AsyncSessionLocal
        from db.models import Project
        from sqlalchemy import select
        from core.agi.cognitive.teleology_engine import teleology_engine
        from core.agi.cognitive.swarm_cortex import swarm_cortex

        print("[OK] Modules imported.")

        # Simulate a minimal mind cycle by calling the components manually
        # 1. Provide fake context
        swarm_cortex.shared_state["global_context"] = "System is missing unit tests for the AGI core."

        # 2. Run the Teleology Engine manually
        wisdom = [
            {"cognitive_health": "Optimal"},
            swarm_cortex.shared_state
        ]
        print("\n[STEP 1] Running Teleology Engine...")
        missions = await teleology_engine.synthesize_missions(wisdom)
        print(f"[OK] Teleology synthesized {len(missions)} missions.")
        for m in missions:
            print(f"  -> {m.get('raw_proposal', '')[:100]}...")

        # 3. Simulate Mind Cycle execution
        print("\n[STEP 2] Running full Mind Cycle (creates background tasks if confident)...")
        async with AsyncSessionLocal() as db:
            nco = NeuralCoreOrchestrator()
            await nco.run_mind_cycle(db)

        # 4. Check if an Autonomous project was created
        print("\n[STEP 3] Verifying Database for Autonomous Project...")
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Project).where(Project.source == "agi_teleology"))
            projs = result.scalars().all()
            print(f"[OK] Found {len(projs)} active Autonomous Projects in DB.")
            for p in projs[-3:]: # latest 3
                print(f"  -> ID: {p.id} | Title: {p.title} | Status: {p.status}")

        print("\n--- Verification completed successfully. ---")

    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_evolution())
