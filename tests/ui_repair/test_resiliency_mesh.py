import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from libs.db.models.ui_repair_models import (
    UIResiliencyMeshNode, UIClusterFailoverEvent, UIGlobalLoadSteeringDecision,
    UIMeshChaosRun, UIGlobalSLOSnapshot, UIAutomatedPostmortem,
    UIRepairCase, MeshNodeStatus, FailoverTrigger, WorkloadType,
    UITenantProfile, UITenantProjectBinding
)
from libs.db.models.core_models import OperationalIncident
from services.ui_repair.mesh_health_aggregator import MeshHealthAggregator
from services.ui_repair.global_load_steering import GlobalLoadSteering
from services.ui_repair.cluster_failover_manager import ClusterFailoverManager
from services.ui_repair.global_slo_watcher import GlobalSLOWatcher
from services.ui_repair.automated_postmortem_generator import AutomatedPostmortemGenerator

@pytest.fixture
async def setup_mesh_data(db_session: AsyncSession):
    # Create Tenant
    tenant = UITenantProfile(tenant_key="ACME_CORP", tenant_name="Acme Corporation")
    db_session.add(tenant)
    
    # Create Nodes
    node1 = UIResiliencyMeshNode(
        tenant_key="ACME_CORP",
        cluster_key="cluster-eu-west-1",
        region="eu-west-1",
        environment="production",
        status="HEALTHY",
        health_score=100.0,
        capacity_score=100.0,
        cost_score=100.0
    )
    node2 = UIResiliencyMeshNode(
        tenant_key="ACME_CORP",
        cluster_key="cluster-us-east-1",
        region="us-east-1",
        environment="production",
        status="HEALTHY",
        health_score=90.0,
        capacity_score=100.0,
        cost_score=100.0
    )
    db_session.add_all([node1, node2])
    
    # Create Binding
    binding = UITenantProjectBinding(
        tenant_key="ACME_CORP",
        project_key="PROJECT_X",
        cluster_key="cluster-eu-west-1"
    )
    db_session.add(binding)
    
    await db_session.commit()
    return tenant, node1, node2

@pytest.mark.asyncio
async def test_mesh_node_heartbeat_updates_health(db_session: AsyncSession, setup_mesh_data):
    _, node1, _ = setup_mesh_data
    
    await MeshHealthAggregator.process_heartbeat(db_session, "cluster-eu-west-1", {
        "latency_ms": 120,
        "active_repairs": 5,
        "queue_depth": 10,
        "base_health": 95.0
    })
    
    await db_session.refresh(node1)
    assert node1.latency_ms == 120
    assert node1.health_score > 90.0
    assert node1.status == "HEALTHY"

@pytest.mark.asyncio
async def test_mesh_health_marks_degraded_cluster(db_session: AsyncSession, setup_mesh_data):
    _, node1, _ = setup_mesh_data
    
    # High latency and low base health
    await MeshHealthAggregator.process_heartbeat(db_session, "cluster-eu-west-1", {
        "latency_ms": 1000,
        "active_repairs": 15,
        "queue_depth": 60,
        "base_health": 40.0
    })
    
    await db_session.refresh(node1)
    assert node1.health_score < 50.0
    assert node1.status in ["DEGRADED", "SATURATED"]

@pytest.mark.asyncio
async def test_load_steering_selects_healthiest_cluster(db_session: AsyncSession, setup_mesh_data):
    _, node1, node2 = setup_mesh_data
    
    # Make node1 unhealthy
    node1.health_score = 30.0
    node1.status = "DEGRADED"
    await db_session.commit()
    
    steering = GlobalLoadSteering(db_session)
    selected, reason = await steering.select_best_cluster(
        tenant_key="ACME_CORP",
        project_key="PROJECT_X",
        workload_type=WorkloadType.OPENSWE_REPAIR
    )
    
    assert selected == "cluster-us-east-1"
    assert "Optimal score" in reason

@pytest.mark.asyncio
async def test_failover_creates_event(db_session: AsyncSession, setup_mesh_data):
    _, node1, node2 = setup_mesh_data
    
    # Create an active case on node1
    case = UIRepairCase(
        route="/dashboard",
        tenant_key="ACME_CORP",
        project_key="PROJECT_X",
        cluster_key="cluster-eu-west-1",
        status="OPEN"
    )
    db_session.add(case)
    await db_session.commit()
    
    events = await ClusterFailoverManager.trigger_failover(
        db_session, 
        source_cluster="cluster-eu-west-1",
        trigger=FailoverTrigger.HEALTH_DEGRADATION,
        reason="Test Outage"
    )
    
    assert len(events) == 1
    assert events[0].source_cluster_key == "cluster-eu-west-1"
    assert events[0].target_cluster_key == "cluster-us-east-1"
    
    await db_session.refresh(case)
    assert case.cluster_key == "cluster-us-east-1"

@pytest.mark.asyncio
async def test_global_slo_snapshot_created(db_session: AsyncSession, setup_mesh_data):
    snapshot = await GlobalSLOWatcher.create_snapshot(db_session)
    assert snapshot.federation_health_score > 0
    assert snapshot.repair_success_rate >= 0

@pytest.mark.asyncio
async def test_automated_postmortem_generation(db_session: AsyncSession, setup_mesh_data):
    # Create incident
    incident = OperationalIncident(
        incident_type="SYSTEM_FAILURE",
        severity="HIGH",
        message="Cluster node vanished",
        status="OPEN"
    )
    db_session.add(incident)
    await db_session.commit()
    
    pm = await AutomatedPostmortemGenerator.generate_for_incident(
        db_session, str(incident.id), "ACME_CORP"
    )
    
    assert pm.title.startswith("Incident Post-Mortem")
    assert pm.tenant_key == "ACME_CORP"
    assert "Incident Detected" in str(pm.timeline_json)
