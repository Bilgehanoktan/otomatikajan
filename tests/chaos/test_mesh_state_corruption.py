import pytest
import asyncio
import os
from services.orchestration.mesh_state_store import MeshStateStore, mesh_state_store
from services.orchestration.mesh_router import MeshRouter
from services.orchestration.federation_router import FederationTask

@pytest.mark.asyncio
async def test_state_corruption_fallback():
    """
    Scenario:
    - The persistent state store (mesh_state.json) is corrupted (invalid data).
    - The Router must detect this and fall back to the last known safe baseline.
    """
    corrupt_path = "configs/corrupt_mesh_state.json"
    
    # 1. Create a corrupted file (Invalid JSON)
    with open(corrupt_path, "w") as f:
        f.write("NOT_A_JSON_OBJECT_{[[[")

    # 2. Re-initialize store with corrupt file
    corrupt_store = MeshStateStore(storage_path=corrupt_path)
    # The store should have initialized with empty defaults due to Exception catch
    assert corrupt_store._state["regions"] == {}

    # 3. Verify Router Fallback
    router = MeshRouter()
    # Mocking the store injected into router for testing
    import services.orchestration.mesh_router as mr_module
    old_store = mr_module.mesh_state_store
    mr_module.mesh_state_store = corrupt_store

    dummy_task = FederationTask(
        task_id="corruption-task",
        project_id="test-project",
        goal_description="Verify fallback",
        required_expertise=["logic"],
        context={}
    )

    # Router should return a fallback route instead of crashing
    routing = await router.route_task_to_mesh(dummy_task)
    
    assert routing is not None
    assert routing.target_region_id == "us-east-1" # Hardcoded fallback
    print(f"\n[SUCCESS] Router gracefully handled state corruption and fell back to {routing.target_region_id}")

    # Cleanup
    mr_module.mesh_state_store = old_store
    if os.path.exists(corrupt_path):
        os.remove(corrupt_path)

if __name__ == "__main__":
    asyncio.run(test_state_corruption_fallback())
