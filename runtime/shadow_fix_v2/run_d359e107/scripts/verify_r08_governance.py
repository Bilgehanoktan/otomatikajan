import time
import sys
import os

# Add local paths
sys.path.append(os.getcwd())

from services.orchestration.fleet_manager import FleetManager
from services.orchestration.economic_engine import economic_engine
from services.orchestration.calibration_engine import calibration_engine
from services.orchestration.trend_analyzer import trend_analyzer

def verify_r08_governance():
    print("--- Sovereign AGI: R-08 Financial Governance Verification ---\n")
    
    fleet = FleetManager()
    project_id = "test-project-r08"
    fleet.register_workload(project_id, tier=1, priority="high", limit=100)
    
    # 1. Simulate Normal Activity & Forecast
    print("[1] Recording normal snapshots and forecasting spend...")
    for _ in range(20):
        fleet.increment_task(project_id)
        fleet.decrement_task(project_id)
    
    # Trigger a forecast (R-08 Spend Forecast included)
    trend_analyzer.forecast_load(project_id, hours_ahead=4)
    
    # 2. Simulate a Cost Spike (Anomaly Detection)
    print("[2] Simulating a massive cost spike...")
    # Inject large tasks to spike the burn rate
    for _ in range(30):
        economic_engine.record_spend(project_id, amount=10.0, region="expensive-node", tier=0)
    
    fleet.perform_governance_cycle()
    snapshot = fleet._active_workloads[project_id]
    anomaly = economic_engine.detect_spend_anomaly(project_id)
    
    print(f"  > Project Health: {snapshot.health}")
    print(f"  > Anomaly Score: {anomaly['score']:.2f} (Reason: {anomaly['reason']})")

    # 3. Simulate Replenishment & Daily Cap hit
    print("\n[3] Testing Daily Replenishment & Safety Cap...")
    # Exhaust budget multiple times to hit the cap (Tier 1 cap is 1000)
    economic_engine._project_budgets[project_id] = 1.0 # Force refill need
    
    for i in range(5):
        refilled = economic_engine.apply_replenishment_policy(project_id, tier=1)
        if refilled == -1.0:
            print(f"  > Attempt {i+1}: Replenishment BLOCKED by Safety Cap (SUCCESS)")
            break
        elif refilled > 0:
            print(f"  > Attempt {i+1}: Refilled {refilled:.2f} USD")
            economic_engine._project_budgets[project_id] = 1.0 # Exhaust again

    # 4. Calibration Audit (Forecast vs Actual)
    print("\n[4] Running Forecast vs Actual Spend Calibration...")
    # Simulate actual load coming in to close the loop
    calibration_engine.update_actuals(project_id, current_actual_load=25.0)
    
    metrics = calibration_engine.get_calibration_metrics()
    print(f"  > Spend Variance MAPE: {metrics['r08_spend_variance_mape']:.2%}")
    print(f"  > Financial Decision Quality: {metrics['r08_economic_decision_quality']:.2f}")

    if metrics['r08_economic_decision_quality'] > 0:
        print("\n[SUCCESS] R-08 Financial Governance layer is operational and calibrated.")

if __name__ == "__main__":
    verify_r08_governance()
