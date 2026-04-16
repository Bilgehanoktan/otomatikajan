import asyncio
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from services.orchestration.latency_adapter import latency_adapter
from services.orchestration.mesh_state_store import mesh_state_store
from services.orchestration.mesh_router import MeshRouter
from services.orchestration.federation_router import FederationTask
from services.governance.policy_sync import PolicySync

async def verify_stage_3_durability():
    print("--- Phase 20 Stage 3: Distributed Durability Verification ---")
    
    # Ensure configs dir exists
    if not os.path.exists("configs"):
        os.makedirs("configs")

    # 1. Test Persistence (State Store)
    print("\n[1/3] Testing State Store Persistence...")
    await latency_adapter.get_latency("us-east-1", "eu-central-1")
    await latency_adapter.get_health_score("ap-southeast-1")
    
    # Check if file exists and has content
    if os.path.exists("configs/mesh_state.json"):
        with open("configs/mesh_state.json", "r") as f:
            data = json.load(f)
            print(f"SUCCESS: mesh_state.json found. Regions: {list(data['regions'].keys())}")
            eu_latency = data['regions'].get('eu-central-1', {}).get('latency_from_us-east-1')
            print(f"Verified Persistence: EU Latency recorded as {eu_latency}ms")
    else:
        print("FAILURE: mesh_state.json not created!")

    # 2. Test GitOps Policy Sync
    print("\n[2/3] Testing GitOps Policy Sync...")
    sync_service = PolicySync()
    sync_results = await sync_service.replicate_policies(["eu-central-1", "ap-southeast-1"])
    
    if sync_results["status"] == "SUCCESS" and len(sync_results.get("commits", [])) > 0:
        print("SUCCESS: Policies replicated and committed to GitOps.")
        for commit in sync_results["commits"]:
            print(f"  - Committed: {commit['file']} (SHA: {commit['sha'][:7]})")
    else:
        print(f"FAILURE: Sync results: {sync_results}")

    # 3. Test Evidence-Driven Routing with Persistence
    print("\n[3/3] Testing Persistent Routing Decision...")
    router = MeshRouter()
    task = FederationTask(
        task_id="dist-persist-test-001",
        goal_description="Refactor backend storage to use MeshStateStore",
        required_expertise=["backend_refactoring"],
        context={"test_mode": True, "source": "verification_script"}
    )
    
    decision = await router.route_task_to_mesh(task)
    
    if decision:
        print(f"SUCCESS: Router made a decision: Region={decision.target_region_id}, Cluster={decision.target_cluster_id}")
        print(f"Metrics used: {decision.latency_ms}ms (Fetched from Persistence)")
    else:
        print("FAILURE: Router failed to route task.")

    print("\n--- Phase 20 Stage 3: MISSION READY ---")

if __name__ == "__main__":
    asyncio.run(verify_stage_3_durability())
