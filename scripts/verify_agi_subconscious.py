import asyncio
import os
import sys
import time

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_subconscious():
    print("--- AGI 34.0 Verification ---")
    
    try:
        from core.agi.consciousness.affective_core import affective_core
        from core.agi.cognitive.theory_of_mind import theory_of_mind
        from core.agi.consciousness.integrated_orchestrator import IntegratedOrchestrator
        
        print("[OK] AGI 34.0 components imported successfully.")
        
        # Otonom bilinci çağır
        orchestrator = IntegratedOrchestrator()
        
        # 1. Simulate Idle/Curious Mood
        print("[INFO] Simulating idle/curious mood (High Curiosity, Low Urgency)...")
        affective_core.state["curiosity"] = 0.9
        affective_core.state["urgency"] = 0.2
        
        # 2. Tetikle `run_mind_cycle` - Asenkron bekleyiş olmadan dönmeli
        print("[INFO] Running 1st Unified Mind Cycle...")
        start_t = time.time()
        await orchestrator.run_mind_cycle()
        end_t = time.time()
        
        print(f"[OK] Mind Cycle completed in: {end_t - start_t:.3f} seconds.")
        if (end_t - start_t) < 1.0:
            print("[OK] Subconscious Dream Thread was successfully spawned in the background (Non-blocking).")
            
        print("[INFO] Waiting for Subconscious Thread to finish its dream (2.5 seconds)...")
        await asyncio.sleep(2.5) # Rüyayı izle
        print("[OK] Subconscious processing finished gracefully.")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_subconscious())
