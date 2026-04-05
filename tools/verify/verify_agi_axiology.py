import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_axiology_intelligence():
    print("--- AGI 27.0 Verification ---")
    
    try:
        from packages.orchestration.agi.cognitive.axiology_engine import axiology_engine
        from packages.orchestration.agi.monitoring.value_auditor import value_auditor
        
        print("[OK] AGI 27.0 components imported successfully.")
        
        # 1. Test Value Auditor
        mock_db = MagicMock()
        print("[INFO] Value Auditor: Running system drift audit...")
        report = await value_auditor.audit_system_drift(mock_db)
        
        if report.get("status") == "Healthy":
            print(f"[OK] Value Auditor: System alignment check passed. Score: {report.get('system_alignment_score')}")
        else:
            print(f"[WARN] Value Auditor: Potential alignment drift detected: {report}")

        # 2. Test Axiology Engine
        print("[INFO] Axiology Engine: Evaluating alignment for a sample plan...")
        mock_plan = "Task: Update database schema; Risk: Potential downtime."
        evaluation = await axiology_engine.evaluate_alignment(mock_plan, "Schema Plan")
        
        if evaluation.get("status") == "audited":
            print(f"[OK] Axiology Engine: Successfully performed ethical evaluation of the target.")
            print(f"    - Report excerpt: {evaluation['alignment_report'][:100]}...")
        else:
            print(f"[ERROR] Axiology Engine failed evaluation: {evaluation}")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_axiology_intelligence())
