from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict, Any, Optional
import uuid
import json

from libs.db.session import get_db
from libs.db.models.core_models import AgentStatus, AgentRole, FleetStatus, AgentNode, FleetCluster
from libs.db.models.governance_models import ProofEventType, GovernanceProofEventRecord
from services.orchestration.fleet.fleet_scheduler import FleetScheduler
from services.orchestration.fleet.multi_project_controller import MultiProjectController
from services.governance.fleet_observability import FleetObservability

from pydantic import BaseModel, Field
from datetime import datetime

# --- Response Schemas ---
class FleetMetricsOut(BaseModel):
    active_agents: int
    idle_agents: int
    busy_agents: int
    quarantined_agents: int
    queued_projects: int
    busy_ratio: float
    budget_burn: float
    cluster_count: int

class FleetClusterOut(BaseModel):
    id: str
    name: str
    status: str
    current_load: float
    agent_count: int
    budget_usage_pct: float

class FleetAgentOut(BaseModel):
    id: str
    name: str
    role: AgentRole
    status: AgentStatus
    trust_score: float = Field(..., ge=0, le=1)
    current_load: int
    last_heartbeat: Optional[datetime] = None
    cluster_id: Optional[str] = None

    class Config:
        from_attributes = True

class FleetEventOut(BaseModel):
    id: str
    event_type: ProofEventType
    entity_id: Optional[str] = None
    payload_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

router = APIRouter(prefix="/fleet", tags=["Orchestration"])

@router.get("/agents", response_model=List[FleetAgentOut])
async def list_agents(
    role: Optional[AgentRole] = None, 
    status: Optional[AgentStatus] = None, 
    cluster_id: Optional[uuid.UUID] = None, 
    db: AsyncSession = Depends(get_db)
):
    query = select(AgentNode)
    if role:
        query = query.where(AgentNode.role == role)
    if status:
        query = query.where(AgentNode.status == status)
    if cluster_id:
        query = query.where(AgentNode.cluster_id == cluster_id)
    
    result = await db.execute(query)
    agents = result.scalars().all()
    
    return [
        FleetAgentOut(
            id=str(a.id),
            name=a.name,
            role=a.role,
            status=a.status,
            trust_score=a.trust_score,
            current_load=a.current_load,
            last_heartbeat=a.last_heartbeat,
            cluster_id=str(a.cluster_id) if a.cluster_id else None
        ) for a in agents
    ]

@router.get("/clusters", response_model=List[FleetClusterOut])
async def list_clusters(db: AsyncSession = Depends(get_db)):
    query = select(FleetCluster)
    result = await db.execute(query)
    clusters = result.scalars().all()
    
    out = []
    for c in clusters:
        usage = c.current_budget_usage / c.budget_limit * 100 if c.budget_limit > 0 else 0
        agent_count = await db.scalar(
            select(func.count(AgentNode.id)).where(AgentNode.cluster_id == c.id)
        ) or 0
        out.append(FleetClusterOut(
            id=str(c.id),
            name=c.name,
            status=c.status.value if hasattr(c.status, "value") else str(c.status),
            current_load=usage,
            agent_count=agent_count,
            budget_usage_pct=usage
        ))
    return out

@router.get("/metrics", response_model=FleetMetricsOut)
async def get_fleet_metrics(db: AsyncSession = Depends(get_db)):
    obs = FleetObservability(db)
    return await obs.aggregate_fleet_metrics()

@router.get("/events", response_model=List[FleetEventOut])
async def list_fleet_events(limit: int = 10, db: AsyncSession = Depends(get_db)):
    fleet_event_types = [
        ProofEventType.AGENT_ASSIGNED, 
        ProofEventType.AGENT_QUARANTINED, 
        ProofEventType.BUDGET_BLOCK, 
        ProofEventType.CLUSTER_FROZEN, 
        ProofEventType.FLEET_REBALANCED,
        ProofEventType.AGENT_RELEASED
    ]
    
    query = (
        select(GovernanceProofEventRecord)
        .where(GovernanceProofEventRecord.event_type.in_(fleet_event_types))
        .order_by(GovernanceProofEventRecord.chain_index.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    events = []
    for r in records:
        summary = None
        try:
            p = json.loads(r.payload_canonical)
            summary = p.get("details") or p.get("msg") or p.get("reason")
        except:
            summary = r.payload_canonical[:100] if r.payload_canonical else None

        events.append(FleetEventOut(
            id=str(r.id),
            event_type=r.event_type,
            entity_id=r.entity_id,
            payload_summary=summary,
            created_at=r.created_at
        ))
    return events

# --- Mutations ---
# Note: For mutations that use sync services (FleetScheduler, etc.), 
# we wrap them in run_sync to maintain thread safety with the async session.

@router.post("/projects/{project_id}/schedule")
async def schedule_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    def _sync_op(sync_db):
        scheduler = FleetScheduler(sync_db)
        return scheduler.schedule_project(project_id)
    
    success = await db.run_sync(_sync_op)
    if not success:
        return {"status": "deferred", "reason": "Resources or budget unavailable"}
    return {"status": "scheduled"}

@router.post("/projects/{project_id}/pause")
async def pause_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    def _sync_op(sync_db):
        controller = MultiProjectController(sync_db)
        controller.pause_project(project_id)
    
    await db.run_sync(_sync_op)
    return {"status": "paused"}

@router.post("/agents/{agent_id}/quarantine")
async def quarantine_agent(agent_id: uuid.UUID, reason: str, db: AsyncSession = Depends(get_db)):
    from services.orchestration.fleet.agent_registry import AgentRegistry
    def _sync_op(sync_db):
        registry = AgentRegistry(sync_db)
        registry.mark_agent_quarantined(agent_id, reason)
    
    await db.run_sync(_sync_op)
    return {"status": "quarantined"}

@router.post("/rebalance")
async def trigger_rebalance(db: AsyncSession = Depends(get_db)):
    def _sync_op(sync_db):
        scheduler = FleetScheduler(sync_db)
        scheduler.rebalance_fleet()
    
    await db.run_sync(_sync_op)
    return {"status": "rebalance_triggered"}
