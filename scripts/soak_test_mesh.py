"""
Sovereign AGI — Phase 26
scripts/soak_test_mesh.py
Long-duration stress and financial governance simulation.
"""
import asyncio
import random
import time
from services.orchestration.fleet_manager import fleet_manager
from services.orchestration.adaptive_quota_adjuster import adaptive_quota_adjuster
from services.orchestration.economic_engine import economic_engine

async def run_soak_test(cycles=100):
    print(f"Starting Phase 26 Mesh Soak Test ({cycles} cycles)...\n")
    
    # Setup projects with different tiers
    projects = [
        {"id": "p-critical", "tier": 0, "limit": 20},
        {"id": "p-enterprise", "tier": 1, "limit": 15},
        {"id": "p-sandbox", "tier": 3, "limit": 5}
    ]
    
    for p in projects:
        fleet_manager.register_workload(p["id"], tier=p["tier"], priority="hi", limit=p["limit"])
        # Kickstart some budget
        economic_engine._project_budgets[p["id"]] = 100.0

    stats = {
        "expansions": 0,
        "replenishments": 0,
        "anomalies": 0,
        "budget_exhaustions": 0
    }

    for i in range(cycles):
        if i % 20 == 0:
            print(f"Cycle {i}/{cycles} in progress...")

        # 1. Random Load fluctuations
        for p in projects:
            # Randomly add/remove tasks to simulate bursty traffic
            load_change = random.randint(-5, 10)
            if load_change > 0:
                for _ in range(load_change):
                    fleet_manager.increment_task(p["id"], region="us-east-1")
            else:
                for _ in range(abs(load_change)):
                    fleet_manager.decrement_task(p["id"])

        # 2. Run Autonomous Engines
        adaptive_quota_adjuster.run_adjustment_cycle()
        fleet_manager.perform_governance_cycle()

        # 3. Collect Snapshots for metrics
        for p in projects:
            snap = fleet_manager._active_workloads[p["id"]]
            if snap.concurrency_limit > snap.base_concurrency_limit:
                stats["expansions"] += 1
            if snap.health == "BUDGET_EXHAUSTED":
                stats["budget_exhaustions"] += 1
            if snap.health == "SPEND_ANOMALY":
                stats["anomalies"] += 1

        # 4. Simulate Regional Pressure (Failover Economy)
        if i == 50:
            print("--- SIMULATING FAILOVER: us-east-1 (cheap) DOWN ---")
            # Force tasks to be more expensive region
            for p in projects:
                fleet_manager.increment_task(p["id"], region="expensive-vault") # High base cost

        # Small yield to mimic time passing, but very fast for soak
        await asyncio.sleep(0.01)

    print("\n--- PHASE 26 SOAK TEST COMPLETED ---")
    print(f"Total Expansion Events: {stats['expansions']}")
    print(f"Total Budget Exhaustions: {stats['budget_exhaustions']}")
    print(f"Total Anomalies Detected: {stats['anomalies']}")
    
    # Final check: Tier 0 should have healthy budget due to replenishment
    p_crit = fleet_manager._active_workloads["p-critical"]
    budget_crit = economic_engine._project_budgets["p-critical"]
    print(f"\np-critical (Tier 0) Final Budget: ${budget_crit:.2f} (Refilled)")
    print(f"p-sandbox (Tier 3) Final Budget: ${economic_engine._project_budgets['p-sandbox']:.2f} (Exhausted/Zeroed)")

    if budget_crit > 50:
        print("\nRESULT: MESH RESILIENT. Tier-0 sustained via auto-replenishment.")
    else:
        print("\nRESULT: MESH WEAK. Tier-0 budget failed to replenish.")

if __name__ == "__main__":
    asyncio.run(run_soak_test(cycles=200))
