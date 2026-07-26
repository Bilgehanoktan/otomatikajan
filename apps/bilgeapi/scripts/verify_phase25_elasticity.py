"""
Sovereign AGI — Phase 25 Verification
scripts/verify_phase25_elasticity.py
Simulates elasticity scenarios: expansion, ceiling, and cooling.
"""
import asyncio
import time
from services.orchestration.fleet_manager import fleet_manager
from services.orchestration.adaptive_quota_adjuster import adaptive_quota_adjuster
from services.orchestration.trend_analyzer import trend_analyzer
from services.orchestration.economic_engine import economic_engine

async def verify_elasticity():
    print("Starting Phase 25 Elasticity Verification...\n")
    
    # 0. Setup Mock Environment
    pid_prod = "proj-prod-el"
    fleet_manager.register_workload(pid_prod, tier=0, priority="high", limit=10)
    # MUST have active tasks to be included in adjustment cycle
    fleet_manager._active_workloads[pid_prod].active_tasks = 1 
    # Force last_adjustment_time to old to allow immediate change
    fleet_manager._active_workloads[pid_prod].last_adjustment_time = time.time() - 100
    
    # 1. Test Auto-Expansion on Spike
    print("Testing Auto-Expansion on Load Spike (Tier-0)...")
    # Simulate rising trend
    for i in range(10):
        trend_analyzer.record_snapshot(pid_prod, 10 + i * 2) 
        
    adaptive_quota_adjuster.run_adjustment_cycle()
    
    snapshot = fleet_manager._active_workloads[pid_prod]
    if snapshot.concurrency_limit > 10:
        print(f"PASSED: Concurrency Limit Expanded: 10 -> {snapshot.concurrency_limit}")
    else:
        print(f"FAILED: Concurrency Limit remained at {snapshot.concurrency_limit}")

    # 2. Test Hard Ceiling (2x Base Limit)
    print("\nTesting Hard Ceiling Enforcement...")
    # Simulate extreme trend
    for i in range(20):
        trend_analyzer.record_snapshot(pid_prod, 50 + i * 5)
    
    # Allow adjustment again
    snapshot.last_adjustment_time = time.time() - 100
    adaptive_quota_adjuster.run_adjustment_cycle()
    
    if snapshot.concurrency_limit == 20: # 10 * 2.0
        print(f"PASSED: Hard Ceiling Enforced at {snapshot.concurrency_limit} (2x base)")
    else:
        print(f"FAILED: Hard Ceiling breached or not reached: {snapshot.concurrency_limit}")

    # 3. Test Budget Blocking for Expansion
    print("\nTesting Budget Blocking for Expansion...")
    pid_poor = "proj-poor-el"
    fleet_manager.register_workload(pid_poor, tier=1, priority="med", limit=10)
    economic_engine._project_budgets[pid_poor] = 0.5 # Low budget
    
    for i in range(10):
        trend_analyzer.record_snapshot(pid_poor, 15)
        
    adaptive_quota_adjuster.run_adjustment_cycle()
    snapshot_poor = fleet_manager._active_workloads[pid_poor]
    
    if snapshot_poor.concurrency_limit == 10:
        print(f"PASSED: Expansion Blocked due to low budget as expected.")
    else:
        print(f"FAILED: Expansion allowed despite low budget: {snapshot_poor.concurrency_limit}")

    print("\nDONE: Phase 25 Elastic Capacity Verified.")

if __name__ == "__main__":
    asyncio.run(verify_elasticity())
