import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_teleology_intelligence():
    print("--- AGI 29.0 Verification ---")
    
    try:
        from packages.orchestration.agi.cognitive.teleology_engine import teleology_engine
        from packages.orchestration.agi.adaptation.goal_prioritizer import goal_prioritizer
        
        print("[OK] AGI 29.0 components imported successfully.")
        
        # 1. Test Teleology Engine
        mock_wisdom = [{"category": "coding", "content": "Expert in Python/AGI patterns"}]
        print("[INFO] Teleology Engine: Synthesizing autonomous missions...")
        missions = await teleology_engine.synthesize_missions(mock_wisdom)
        
        if len(missions) > 0:
            print(f"[OK] Teleology Engine: Successfully synthesized {len(missions)} mission(s).")
            print(f"    - Raw Proposal: {missions[0].get('raw_proposal')[:100]}...")
        else:
            print("[WARN] Teleology Engine: No missions synthesized.")

        # 2. Test Goal Prioritizer
        print("[INFO] Goal Prioritizer: Ranking synthesized missions...")
        # Mock mission from LLM structure
        proposed = [{"title": "AGI Self-Expansion", "content": "Build new layers"}] 
        ranked = await goal_prioritizer.prioritize_goals(proposed)
        
        if len(ranked) > 0:
            print(f"[OK] Goal Prioritizer: Successfully ranked missions. Top priority: {ranked[0].get('title')}")
            print(f"    - Priority Score: {ranked[0].get('priority_score')}")
        else:
            print("[ERROR] Goal Prioritizer failed to rank missions.")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_teleology_intelligence())
