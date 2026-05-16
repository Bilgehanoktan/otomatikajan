import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.session import get_db
from services.ui_repair.schemas import (
    UIResiliencyMeshNodeSchema, UIResiliencyMeshNodeCreate,
    UIClusterFailoverEventSchema, UIGlobalLoadSteeringDecisionSchema,
    UIMeshChaosRunSchema, UIGlobalSLOSnapshotSchema,
    UIAutomatedPostmortemSchema, WorkloadType, FailoverTrigger
)
from services.ui_repair.mesh_health_aggregator import MeshHealthAggregator
from services.ui_repair.global_load_steering import GlobalLoadSteering
from services.ui_repair.cluster_failover_manager import ClusterFailoverManager
from services.ui_repair.cross_cluster_chaos_runner import CrossClusterChaosRunner
from services.ui_repair.global_slo_watcher import GlobalSLOWatcher
from services.ui_repair.automated_postmortem_generator import AutomatedPostmortemGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mesh", tags=["Resiliency Mesh"])

@router.get("/health", response_model=Dict[str, Any])
async def get_mesh_health(db: AsyncSession = Depends(get_db)):
    """Returns the aggregated health of the resiliency mesh."""
    return await MeshHealthAggregator.get_mesh_status(db)

@router.post("/nodes/heartbeat")
async def register_node_heartbeat(
    cluster_key: str, 
    metrics: Dict[str, Any], 
    db: AsyncSession = Depends(get_db)
):
    """Processes a heartbeat from a federated cluster node."""
    await MeshHealthAggregator.process_heartbeat(db, cluster_key, metrics)
    return {"status": "ACK"}

@router.get("/nodes", response_model=List[UIResiliencyMeshNodeSchema])
async def list_mesh_nodes(db: AsyncSession = Depends(get_db)):
    """Lists all nodes in the resiliency mesh."""
    from sqlalchemy import select
    from libs.db.models.ui_repair_models import UIResiliencyMeshNode
    stmt = select(UIResiliencyMeshNode)
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.post("/load-steering/evaluate")
async def evaluate_steering(
    tenant_key: str,
    project_key: str,
    workload_type: WorkloadType,
    db: AsyncSession = Depends(get_db)
):
    """Evaluates the best cluster for a given workload."""
    steering = GlobalLoadSteering(db)
    cluster, reason = await steering.select_best_cluster(tenant_key, project_key, workload_type)
    if not cluster:
        raise HTTPException(status_code=400, detail=reason)
    return {"selected_cluster": cluster, "reason": reason}

@router.post("/failover/trigger")
async def trigger_failover(
    cluster_key: str,
    trigger: FailoverTrigger,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    """Manually triggers a cluster failover."""
    events = await ClusterFailoverManager.trigger_failover(db, cluster_key, trigger, reason)
    return {"triggered": True, "event_count": len(events)}

@router.get("/failover/events", response_model=List[UIClusterFailoverEventSchema])
async def list_failover_events(db: AsyncSession = Depends(get_db)):
    """Lists all failover events."""
    from sqlalchemy import select
    from libs.db.models.ui_repair_models import UIClusterFailoverEvent
    stmt = select(UIClusterFailoverEvent).order_by(UIClusterFailoverEvent.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.post("/chaos/run", response_model=UIMeshChaosRunSchema)
async def run_chaos_drill(
    scenario: str,
    cluster_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Executes a chaos engineering drill."""
    return await CrossClusterChaosRunner.run_scenario(db, scenario, cluster_key)

@router.get("/slo/global", response_model=UIGlobalSLOSnapshotSchema)
async def get_global_slo(db: AsyncSession = Depends(get_db)):
    """Returns the latest global SLO snapshot."""
    return await GlobalSLOWatcher.create_snapshot(db)

@router.post("/postmortem/generate", response_model=UIAutomatedPostmortemSchema)
async def generate_postmortem(
    incident_id: str,
    tenant_key: str,
    db: AsyncSession = Depends(get_db)
):
    """Generates an automated post-mortem for an incident."""
    return await AutomatedPostmortemGenerator.generate_for_incident(db, incident_id, tenant_key)
