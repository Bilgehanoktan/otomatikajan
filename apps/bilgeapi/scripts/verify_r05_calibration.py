import os
import sys
import time
from typing import Dict, Any

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.orchestration.calibration_engine import calibration_engine

def verify_r05_calibration():
    print("\n--- STARTING R-05 SELF-CORRECTION SECURITY CALIBRATION ---")
    
    # Reset history for clean test
    calibration_engine._correction_history = []

    # [STEP 1] Simulate 10 Proposals
    print("[STEP 1] Generating 10 Patch Proposals...")
    for i in range(10):
        calibration_engine.record_correction(
            incident_id=f"inc_{i}",
            action="proposal",
            risk_score=0.15 + (i * 0.05),
            severity="medium"
        )

    # [STEP 2] Simulate 8 Canary Successes (Good Patches)
    print("[STEP 2] Recording 8 Successful Canary Promotions...")
    for i in range(8):
        calibration_engine.record_correction(
            incident_id=f"prom_{i}",
            action="canary_success",
            risk_score=0.2,
            is_success=True
        )

    # [STEP 3] Simulate 2 Canary Failures & Rollbacks (Wrong Patches)
    print("[STEP 3] Recording 2 Canary Failures & Emergency Rollbacks...")
    for i in range(2):
        calibration_engine.record_correction(
            incident_id=f"fail_{i}",
            action="canary_fail",
            risk_score=0.4,
            is_success=False # Patch killed health
        )
        calibration_engine.record_correction(
            incident_id=f"fail_{i}",
            action="rollback",
            risk_score=0.4,
            is_success=True # Revert helped
        )

    # [STEP 4] Simulate 1 Unnecessary Rollback (False Alarm)
    print("[STEP 4] Recording 1 Unnecessary Rollback (False Alarm)...")
    calibration_engine.record_correction(
        incident_id="false_alarm_1",
        action="rollback",
        risk_score=0.2,
        is_success=False # Revert did NOT help health
    )

    # [STEP 5] Simulate 2 Conservative Gate Blocks (High Risk, Low Severity)
    print("[STEP 5] Recording 2 Conservative Gate Blocks...")
    for i in range(2):
        calibration_engine.record_correction(
            incident_id=f"gate_{i}",
            action="blocked_by_gate",
            risk_score=0.85, # High risk
            severity="low"   # Low severity incident
        )

    # [STEP 6] Calculate Calibration Results
    print("\n--- R-05 CALIBRATION REPORT ---")
    metrics = calibration_engine.get_calibration_metrics()
    
    # R-05 Evaluation
    patch_success = metrics["r05_patch_success_rate"]
    wrong_patch = metrics["r05_wrong_patch_rate"]
    unnecessary_rb = metrics["r05_unnecessary_rollback_rate"]
    conservative_block = metrics["r05_conservative_block_rate"]
    
    print(f"Patch Success Rate:      {patch_success*100:0.2f}%")
    print(f"Wrong Patch Rate:        {wrong_patch*100:0.2f}%")
    print(f"Unnecessary Rollbacks:   {unnecessary_rb*100:0.2f}%")
    print(f"Conservative Blocks:     {conservative_block*100:0.2f}%")
    
    print(f"Sample Size (Corrections): {metrics['samples']['corrections']}")

    # Validation Logic
    if patch_success > 0.7 and wrong_patch < 0.3:
        print("\n[SUCCESS] R-05 VERIFICATION PASSED: Self-Correction Calibration Loop Verified.")
    else:
        print("\n[FAILURE] R-05 Calibration out of bounds.")
        sys.exit(1)

if __name__ == "__main__":
    verify_r05_calibration()
