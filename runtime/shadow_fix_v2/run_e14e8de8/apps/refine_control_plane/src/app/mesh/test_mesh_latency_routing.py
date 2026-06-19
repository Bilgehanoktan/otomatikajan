import asyncio
import os
import sys
import yaml

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[5]))

from services.orchestration.federation_router import FederationTask
from services.orchestration.mesh_router import MeshRouter
from services.orchestration.latency_adapter import latency_adapter

async def test_latency_aware_routing():
    print("--- [START] Latency-Aware Routing Test ---")
    
    router = MeshRouter()
    
    # 1. Define a standard logic task
    task = FederationTask(
        task_id="test-mesh-001",
        goal_description="Coordinate global state sync",
        required_expertise=["backend_refactoring"],
        context={"origin": "external"}
    )

    print(f"\n[Test 1] Routing with Baseline Latency...")
    # Baseline: US (5ms), EU (85ms), AP (195ms)
    routing = await router.route_task_to_mesh(task)
    print(f"Result: Region={routing.target_region_id}, Latency={routing.latency_ms}ms")
    assert routing.target_region_id == "us-east-1", "Should pick US (lowest latency baseline)"

    # 2. Simulate EU becoming faster (or US becoming very slow)
    print(f"\n[Test 2] Simulating high latency in US-East-1...")
    latency_adapter.baseline_matrix["us-east-1"]["us-east-1"] = 300.0 # Huge lag in US
    
    routing = await router.route_task_to_mesh(task)
    print(f"Result: Region={routing.target_region_id}, Latency={routing.latency_ms}ms")
    # EU baseline to US source is 85ms, while US to US is now 300ms
    # Actually MeshRouter assumes source is us-east-1 in the code: source_region="us-east-1"
    # So it compares: 
    #   us-east-1 -> us-east-1 (300ms)
    #   us-east-1 -> eu-central-1 (85ms)
    #   us-east-1 -> ap-southeast-1 (195ms)
    # Expected: eu-central-1 (85ms)
    assert routing.target_region_id == "eu-central-1", "Should pivot to EU due to US latency spike"

    print("\n--- [SUCCESS] Latency-Aware Routing Verified ---")

if __name__ == "__main__":
    asyncio.run(test_latency_aware_routing())
