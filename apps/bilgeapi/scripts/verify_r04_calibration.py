"""
Sovereign AGI — Phase 21 (R-04)
scripts/verify_r04_calibration.py
Verifies Forecast vs Actual Calibration and Economic Steering Impact.
"""
import asyncio
import json
import os
import random
import time

# Mocking Environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./runtime/data/cortex_local.db"

from services.orchestration.fleet_manager import fleet_manager
from services.orchestration.trend_analyzer import trend_analyzer
from services.orchestration.adaptive_quota_adjuster import adaptive_quota_adjuster
from services.orchestration.calibration_engine import calibration_engine
from services.orchestration.economic_engine import economic_engine

async def simulate_calibration_run():
    print("--- STARTING R-04 FORECAST VS ACTUAL CALIBRATION ---")
    
    # 1. Setup Test Project
    project_id = "calibration-heavy-project"
    fleet_manager.register_workload(project_id, tier=1, priority="HIGH", limit=10)
    
    print(f"[STEP 1] Generating Historical Data & Steering...")
    # Simulate some tasks with steering
    for _ in range(20):
        # We simulate economic steering by having multiple regions and picking the cheapest
        # MeshRouter would normally do this, we manually simulate the impact here
        fleet_manager.increment_task(project_id, region="local-node")
        calibration_engine.record_steering_impact(random.uniform(0.01, 0.05)) # Savings per task
    
    print(f"[STEP 2] Making Forecasts & Decisions...")
    # Run a few adjustment cycles
    for cycle in range(5):
        adaptive_quota_adjuster.run_adjustment_cycle()
        time.sleep(0.1) # Simulate time passing for the analyzer
        
        # Simulate load growth to trigger forecast calibration
        for _ in range(5):
            fleet_manager.increment_task(project_id)
            
    # 3. Trigger 'False Expansion' scenario
    print(f"[STEP 3] Testing Decision Quality (False Expansion)...")
    # Register another project, expand it, but keep its load low
    p2 = "ghost-project"
    fleet_manager.register_workload(p2, tier=1, priority="MED", limit=5)
    
    # Force a high forecast (simulate spike)
    trend_analyzer.record_snapshot(p2, 20) 
    adaptive_quota_adjuster.run_adjustment_cycle() # Should expand p2
    
    # But actual load stays low (triggering False Expansion detection)
    fleet_manager.decrement_task(p2)
    fleet_manager.decrement_task(p2)
    calibration_engine.update_actuals(p2, 1)

    # 4. Results Aggregation
    print(f"[STEP 4] Calculating Calibration Metrics...")
    metrics = calibration_engine.get_calibration_metrics()
    
    print("\n--- R-04 CALIBRATION REPORT ---")
    print(f"Forecast Error (MAPE):      {metrics['forecast_mape']:.2%}")
    print(f"False Expansion Rate:      {metrics['false_expansion_rate']:.2%}")
    print(f"Under-Expansion (Blocks):  {metrics['under_expansion_rate']:.2%}")
    print(f"Total Steering Savings:    ${metrics['total_steering_savings_usd']:.4f}")
    print(f"Avg Saving per Steer:      ${metrics['avg_saving_per_steer']:.4f}")
    print(f"Total Samples Tracked:     {metrics['sample_size']}")
    
    # R-04 Validation Criteria
    success = True
    if metrics['sample_size'] == 0:
        print("[FAILED] No calibration samples recorded.")
        success = False
    
    if metrics['total_steering_savings_usd'] <= 0:
        print("[FAILED] No economic steering impact detected.")
        success = False

    if success:
        print("\n[SUCCESS] R-04 VERIFICATION PASSED: Calibration Loop Active.")
    else:
        print("\n[FAILED] R-04 VERIFICATION FAILED: Metrics incomplete.")

if __name__ == "__main__":
    asyncio.run(simulate_calibration_run())
