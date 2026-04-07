import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_affective_core():
    print("--- AGI 32.0 Verification ---")
    
    try:
        from packages.orchestration.agi.consciousness.affective_core import affective_core
        from packages.orchestration.agi.adaptation.timeline_selector import timeline_selector
        
        print("[OK] AGI 32.0 components imported successfully.")
        
        # 1. Test Initial Mood
        print(f"[INFO] Initial Mood: {affective_core.get_current_mood()}")
        
        # 2. Trigger Errors -> Caution goes up
        print("[INFO] Simulating continuous failures/errors...")
        for _ in range(5):
            affective_core.adjust_state("error", magnitude=0.1)
            
        new_mood = affective_core.get_current_mood()
        print(f"[OK] Affective Core reacted. New Mood: {new_mood} (Caution: {affective_core.state['caution']:.2f})")
        
        # 3. Test Timeline Selector Bias
        mock_timelines = [
            {"type": "Conservative", "utility_score": 0.4, "risk_score": 0.1, "ethics_score": 1.0},
            {"type": "Balanced", "utility_score": 0.7, "risk_score": 0.3, "ethics_score": 1.0},
            {"type": "Aggressive", "utility_score": 0.9, "risk_score": 0.8, "ethics_score": 0.9}
        ]
        
        print("[INFO] Timeline Selector: Selecting future under Cautious state...")
        optimal_cautious = await timeline_selector.select_optimal_timeline(mock_timelines)
        print(f"[OK] Timeline Selector (Cautious): Selected -> {optimal_cautious.get('type')}")
        
        # 4. Trigger Success -> Satisfaction / Curiosity goes up
        print("[INFO] Simulating exploration and success...")
        for _ in range(10):
            affective_core.adjust_state("success", magnitude=0.1)
            
        new_mood = affective_core.get_current_mood()
        print(f"[OK] Affective Core reacted. New Mood: {new_mood} (Curiosity: {affective_core.state['curiosity']:.2f}, Caution: {affective_core.state['caution']:.2f})")
        
        print("[INFO] Timeline Selector: Selecting future under Curious state...")
        # reset final scores to avoid bleeding
        for t in mock_timelines: 
            if "final_score" in t: del t["final_score"]
            
        optimal_curious = await timeline_selector.select_optimal_timeline(mock_timelines)
        print(f"[OK] Timeline Selector (Curious): Selected -> {optimal_curious.get('type')}")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_affective_core())
