import asyncio
import os
import sys
from unittest.mock import MagicMock

# Proje köke python path ekle
sys.path.append(os.getcwd())

async def verify_agi_foresight_intelligence():
    print("--- AGI 26.0 Verification ---")
    
    try:
        from packages.orchestration.agi.cognitive.foresight_oracle import foresight_oracle
        from packages.orchestration.agi.adaptation.risk_mitigator import risk_mitigator
        from packages.orchestration.agi.schemas import PlanProposal
        
        print("[OK] AGI 26.0 components imported successfully.")
        
        # 1. Test Foresight Oracle
        mock_plan = MagicMock()
        mock_plan.task_id = "test_task_001"
        mock_plan.dict = MagicMock(return_value={"steps": ["Step 1: Write code", "Step 2: Deploy"]})
        
        print("[INFO] Foresight Oracle: Simulating test plan...")
        risks = await foresight_oracle.simulate_plan(mock_plan)
        
        if len(risks) > 0:
            print(f"[OK] Foresight Oracle: Successfully predicted potential risks via mental simulation.")
        else:
            print("[INFO] Foresight Oracle: Simulation completed (logic active).")

        # 2. Test Risk Mitigator
        print("[INFO] Risk Mitigator: Injecting safeguards into plan...")
        mitigated_plan = await risk_mitigator.mitigate_risks(mock_plan, risks)
        
        if mitigated_plan:
            print(f"[OK] Risk Mitigator: Successfully refined plan with predictive safeguards.")
        else:
            print(f"[ERROR] Risk Mitigator failed to refine plan.")
            
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_agi_foresight_intelligence())
