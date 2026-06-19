import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from services.orchestration.mesh_state_store import mesh_state_store
from services.orchestration.mesh_router import MeshRouter, QuorumLossException
from services.orchestration.federation_router import FederationTask

@pytest.mark.asyncio
async def test_region_partition_behavior():
    """
    Scenario:
    - 3 regions (US, EU, AP) are healthy.
    - US and EU lose connectivity (Partitioned).
    - AP becomes the isolated region.
    - Quorum must fail, and Router must block write-ops.
    """
    # 1. Setup healthy mesh
    regions = ["us-east-1", "eu-central-1", "ap-southeast-1"]
    for rid in regions:
        mesh_state_store.set_region_metrics(rid, {"health_status": "NOMINAL"})

    assert mesh_state_store.get_healthy_region_count() == 3
    assert mesh_state_store.is_quorum_maintained() is True

    # 2. Simulate Partition (Kill US and EU pulses)
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    with mesh_state_store._lock:
        mesh_state_store._state["regions"]["us-east-1"]["updated_at"] = old_time
        mesh_state_store._state["regions"]["eu-central-1"]["updated_at"] = old_time
    
    # Check quorum on the isolated region (AP)
    # Healthy regions count should be 1 (only AP)
    assert mesh_state_store.get_healthy_region_count() == 1
    assert mesh_state_store.is_quorum_maintained() is False

    # 3. Verify Router blocks high-risk tasks
    router = MeshRouter()
    dummy_task = FederationTask(
        task_id="chaos-task-001",
        project_id="test-project",
        goal_description="Test under partition",
        required_expertise=["logic"],
        context={"risk": "HIGH"}
    )

    with pytest.raises(QuorumLossException) as excinfo:
        await router.route_task_to_mesh(dummy_task)
    
    assert "Quorum lost" in str(excinfo.value)
    print("\n[SUCCESS] MeshRouter correctly blocked tasks during partition.")

if __name__ == "__main__":
    asyncio.run(test_region_partition_behavior())
