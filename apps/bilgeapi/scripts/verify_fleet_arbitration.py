"""
Sovereign AGI — Phase 23
scripts/verify_fleet_arbitration.py
Simulates mass-scale task routing with Quota Arbitration.
"""
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.orchestration.mesh_router import mesh_router
from services.orchestration.federation_router import FederationTask
from services.orchestration.fleet_manager import fleet_manager

async def run_simulation():
    print("--- STARTING FLEET ARBITRATION STRESS TEST ---")
    
    # 1. Define typical projects with different Tiers
    projects = [
        {"id": "proj-crit", "tier": 0, "limit": 5},   # Mission Critical
        {"id": "proj-norm", "tier": 2, "limit": 10},  # Standard
        {"id": "proj-sand", "tier": 3, "limit": 2},   # Sandbox
    ]
    
    # 2. Burst tasks to exceed Sandbox limits but stay within Critical
    tasks = []
    
    # Critical Project sends 3 tasks (should pass)
    for i in range(3):
        tasks.append(FederationTask(
            task_id=f"crit-{i}", project_id="proj-crit", capability="compute", priority=10
        ))
        
    # Sandbox Project sends 5 tasks (limit is 2, some should fail)
    for i in range(5):
        tasks.append(FederationTask(
            task_id=f"sand-{i}", project_id="proj-sand", capability="compute", priority=1
        ))

    print(f"Dispatched {len(tasks)} tasks to MeshRouter...")
    
    results = []
    for t in tasks:
        try:
            route = await mesh_router.route_task(t)
            results.append({"id": t.task_id, "status": "ROUTED", "region": route.region})
        except Exception as e:
            results.append({"id": t.task_id, "status": "REJECTED", "reason": str(e)})

    # 3. Report
    print("\n--- SIMULATION RESULTS ---")
    for r in results:
        icon = "✅" if r["status"] == "ROUTED" else "❌"
        line = f"{icon} {r['id']}: {r['status']}"
        if "region" in r: line += f" -> {r['region']}"
        if "reason" in r: line += f" ({r['reason']})"
        print(line)

    # 4. Check Fleet Stats
    stats = fleet_manager.get_fleet_stats()
    print(f"\nFleet Stats - Active Projects: {stats['total_projects']}")
    print(f"Tier Usage: {stats['tier_usage']}")

if __name__ == "__main__":
    asyncio.run(run_simulation())
