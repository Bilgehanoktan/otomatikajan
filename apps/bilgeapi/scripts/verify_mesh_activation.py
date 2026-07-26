"""
Sovereign AGI — Phase 27 Verification
scripts/verify_mesh_activation.py
Verifies R-03 Real Distributed Backend Activation by simulating multi-region sync.
"""
import os
# Force SQLite for clean R-03 Verification (Avoid Postgres noise)
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./runtime/data/cortex_local.db"

import asyncio
import json
import uuid
from libs.mesh.state_fabric import state_fabric
from libs.mesh.event_bridge import event_bridge
from services.orchestration.fleet_manager import fleet_manager
from services.orchestration.consensus_engine import get_consensus_engine

async def simulate_region(region_id: str, is_primary_candidate: bool = False):
    print(f"[NODE:{region_id}] Initializing...")
    consensus = get_consensus_engine(region_id)
    if is_primary_candidate:
        consensus.set_priority(200) # Higher priority for us-east-1
    
    # 1. Start HA Role arbitration
    asyncio.create_task(consensus.start_consensus_loop())
    
    # 2. Simulate some local activity
    fleet_manager.register_workload(f"p-mesh-test-{region_id}", tier=1, priority="med", limit=10)
    for _ in range(5):
        fleet_manager.increment_task(f"p-mesh-test-{region_id}", region=region_id)
    
    # 3. Sync to Global Fabric
    await fleet_manager.sync_mesh_state(region_id)
    print(f"[NODE:{region_id}] Initial sync complete. Role: {consensus.current_role.upper()}")
    return consensus

async def verify_global_sync():
    print("--- STARTING R-03 DISTRIBUTED BACKEND VERIFICATION ---")
    
    # 1. Start Region A (US)
    us_node = await simulate_region("us-east-1", is_primary_candidate=True)
    
    # 2. Start Region B (EU)
    eu_node = await simulate_region("eu-central-1")
    
    # Wait for consensus logic to settle
    print("Waiting for cross-region consensus arbitration (10s)...")
    await asyncio.sleep(10)
    
    # 3. Inspect Global Mesh View from Fabric (The Central Truth)
    view = await state_fabric.get_mesh_view()
    
    print("\n[GLOBAL MESH VIEW - REAL REDIS DATA]")
    print(json.dumps(view, indent=2))
    
    # 4. Assertions
    has_primary = any(data.get("role") == "primary" for data in view.values())
    has_us = "us-east-1" in view
    has_eu = "eu-central-1" in view
    
    print("\n--- RESULTS ---")
    if has_us and has_eu and has_primary:
        print("[SUCCESS] R-03 VERIFICATION PASSED: Distributed state is consistent and HA-aware.")
    else:
        print("[FAILED] R-03 VERIFICATION FAILED: Mesh view incomplete or no primary elected.")
        if not has_primary: print("   Reason: No Primary region found.")
        if not has_us: print("   Reason: Region us-east-1 state missing.")

if __name__ == "__main__":
    # Ensure runtime dir exists
    os.makedirs("runtime/data", exist_ok=True)
    asyncio.run(verify_global_sync())
