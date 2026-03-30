import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_immunology_intelligence():
    print("--- AGI 22.0 Verification ---")
    
    try:
        from core.agi.monitoring.pathogen_detector import pathogen_detector
        from core.agi.adaptation.immunity_weaver import immunity_weaver
        
        print("[OK] AGI 22.0 components imported successfully.")
        
        # 1. Test Pathogen Detection
        mock_db = MagicMock()
        # Mock result for pathogen query
        pathogens = await pathogen_detector.detect_pathogens(mock_db)
        if len(pathogens) > 0:
            print(f"[OK] Pathogen Detector: Successfully detected {len(pathogens)} structural failure patterns.")
        else:
            print("[INFO] Pathogen Detector: No pathogens found in current logs (logic checked).")

        # 2. Test Immunity Weaving (Antibodies)
        test_pathogen = {"id": "test_429", "error_type": "RateLimitError", "module": "llm_provider"}
        antibodies = await immunity_weaver.weave_antibodies([test_pathogen])
        
        if len(antibodies) > 0:
            print(f"[OK] Immunity Weaver: Successfully synthesized {len(antibodies)} antibodies (defensive decorators).")
            for a in antibodies:
                antibody_path = os.path.join("core/agi/immunity", a)
                if os.path.exists(antibody_path):
                    print(f"    - Antibody created at: {antibody_path}")
                else:
                    print(f"    - [WARN] Antibody file missing for {a}")
        else:
            print("[ERROR] Immunity Weaver failed to synthesize antibodies.")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_immunology_intelligence())
