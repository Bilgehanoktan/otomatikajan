import pytest
import asyncio
from services.orchestration.mesh_state_store import mesh_state_store
from services.orchestration.mesh_router import MeshRouter
from services.orchestration.federation_router import FederationTask

@pytest.mark.asyncio
async def test_automatic_failover_routing():
    """
    Scenario:
    - Primary Region (us-east-1) experiences a catastrophic failure (Health 0.1).
    - Secondary Region (eu-central-1) is healthy (Health 1.0).
    - Router must automatically select the Secondary region for all new tasks.
    """
    # 1. Setup initial state
    mesh_state_store.set_region_metrics("us-east-1", {
        "health_status": "DEGRADED",
        "health_score": 0.1,
        "latency_from_us-east-1": 1500.0 # High latency simulation
    })
    mesh_state_store.set_region_metrics("eu-central-1", {
        "health_status": "NOMINAL",
        "health_score": 1.0,
        "latency_from_us-east-1": 85.0
    })

    # Update registry mock for test (forcing NOMINAL check to use score)
    # We update the memory regions to reflect common registry structure
    router = MeshRouter()
    for reg in router.regions:
        if reg["id"] == "us-east-1":
            reg["health_status"] = "CRITICAL"
        if reg["id"] == "eu-central-1":
            reg["health_status"] = "NOMINAL"

    # 2. Route a new task
    dummy_task = FederationTask(
        task_id="failover-task-001",
        project_id="test-project",
        goal_description="Verify health-based rerouting",
        required_expertise=["backend_refactoring"],
        context={}
    )

    routing = await router.route_task_to_mesh(dummy_task)

    # 3. Verify EU-CENTRAL-1 was selected
    assert routing is not None
    assert routing.target_region_id == "eu-central-1"
    assert routing.latency_ms == 85.0
    print(f"\n[SUCCESS] Failover triggered. Rerouted from US (CRITICAL) to {routing.target_region_id}")

if __name__ == "__main__":
    asyncio.run(test_automatic_failover_routing())
