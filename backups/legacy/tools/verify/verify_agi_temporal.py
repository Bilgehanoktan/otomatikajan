import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_temporal_intelligence():
    print("--- AGI 24.0 Verification ---")
    
    try:
        from packages.orchestration.agi.cognitive.chronicler import chronicler
        from packages.orchestration.agi.adaptation.temporal_tuner import temporal_tuner
        
        print("[OK] AGI 24.0 components imported successfully.")
        
        # 1. Test Chronicler
        mock_db = MagicMock()
        analysis = await chronicler.analyze_temporal_patterns(mock_db)
        
        if analysis:
            print(f"[OK] Chronicler: Analyzed {analysis.get('sample_size', 0)} project durations.")
            print(f"    - Avg duration: {analysis.get('avg_project_duration_s', 0):.2f}s")
        else:
            print("[INFO] Chronicler: No project history found yet, but logic is active.")

        # 2. Test Temporal Tuner
        # Mock analysis data for tuning
        mock_analysis = {
            "avg_project_duration_s": 150.5,
            "sample_size": 20,
            "recent_history": [{"id": "1", "duration_s": 120}, {"id": "2", "duration_s": 180}]
        }
        tuning_result = await temporal_tuner.tune_temporal_parameters(mock_analysis)
        
        if tuning_result.get("status") == "tuned":
            print(f"[OK] Temporal Tuner: Successfully generated tuning recommendations.")
            print(f"    - Recommendation excerpt: {tuning_result['recommendation'][:100]}...")
        else:
            print(f"[ERROR] Temporal Tuner failed: {tuning_result}")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_temporal_intelligence())
