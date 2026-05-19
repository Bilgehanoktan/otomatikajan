import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_meta_intelligence():
    print("--- AGI 28.0 Verification ---")
    
    try:
        from packages.orchestration.agi.monitoring.meta_audit import meta_audit
        from packages.orchestration.agi.adaptation.metacognitive_tuner import metacognitive_tuner
        
        print("[OK] AGI 28.0 components imported successfully.")
        
        # 1. Test Meta Audit
        mock_db = MagicMock()
        print("[INFO] Meta Audit: Performing self-reflection...")
        reflection = await meta_audit.perform_self_reflection(mock_db)
        
        if reflection.get("cognitive_health") == "Optimal":
            print(f"[OK] Meta Audit: Self-reflection identifies optimal health. Success Rate: {reflection.get('success_rate')}")
        else:
            print(f"[INFO] Meta Audit: Self-reflection logic active. Report: {reflection}")

        # 2. Test Metacognitive Tuner
        print("[INFO] Metacognitive Tuner: Generating meta-thought based on reflection...")
        tuning = await metacognitive_tuner.tune_metacognition(reflection)
        
        if tuning.get("status") == "tuned":
            print(f"[OK] Metacognitive Tuner: Successfully generated meta-cognition block.")
            print(f"    - Metacognition excerpt: {tuning['metacognition'][:100]}...")
        else:
            print(f"[ERROR] Metacognitive Tuner failed: {tuning}")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_meta_intelligence())
