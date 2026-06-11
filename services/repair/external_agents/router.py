import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from libs.db.session import get_db
from libs.db.models.repair_models import AgentCapabilityModel, AgentRunModel, AgentArtifactPromotionModel
from services.auth.jwt_auth import get_current_identity, require_permission
from services.repair.external_agents.agent_sandbox_executor import AgentSandboxExecutor
from services.repair.external_agents.agent_ledger_reporter import AgentLedgerReporter
from services.repair.external_agents.agent_promotion_gate import AgentPromotionGate

router = APIRouter(tags=["Agent Capabilities & Sandbox"])

# Pydantic Schemas
class CapabilityResponse(BaseModel):
    agent_key: str
    agent_name: str
    description: str
    enabled: bool
    risk_level: str
    sandbox_mode: str
    max_cost_limit: float
    requires_human_approval: bool
    network_policy: str
    allowed_domains: List[str]
    allowed_directories: List[str]
    blocked_directories: List[str]
    allowed_commands: List[str]
    blocked_commands: List[str]

    class Config:
        from_attributes = True

class RunCreateRequest(BaseModel):
    agent_key: str = Field(..., example="swe_agent")
    command_handler: str = Field(..., example="run_tests")
    arguments: Dict[str, Any] = Field(default_factory=dict, example={"test_path": "tests/ui_repair"})
    target_paths: List[str] = Field(default_factory=list, example=["tests/ui_repair"])
    cost: float = Field(0.01, example=0.05)
    network_domains: Optional[List[str]] = Field(default_factory=list, example=["localhost"])

class RunResponse(BaseModel):
    run_id: str
    agent_key: str
    status: str
    workspace_path: Optional[str] = None
    exit_code: Optional[int] = None
    cost: float
    started_at: Optional[Any] = None
    completed_at: Optional[Any] = None
    sandbox_mode: str
    network_policy: str
    ledger_chain_id: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/capabilities", response_model=List[CapabilityResponse], summary="List all agent capabilities")
async def list_capabilities(
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.read"))
):
    stmt = select(AgentCapabilityModel)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/capabilities/{agent_key}", response_model=CapabilityResponse, summary="Get details of a specific agent capability")
async def get_capability(
    agent_key: str,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.read"))
):
    stmt = select(AgentCapabilityModel).where(AgentCapabilityModel.agent_key == agent_key)
    res = await db.execute(stmt)
    cap = res.scalars().first()
    if not cap:
        raise HTTPException(status_code=404, detail=f"Agent capability record '{agent_key}' not found.")
    return cap

@router.post("/capabilities/{agent_key}/enable", summary="Enable a registered agent")
async def enable_agent(
    agent_key: str,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.manage"))
):
    stmt = select(AgentCapabilityModel).where(AgentCapabilityModel.agent_key == agent_key)
    res = await db.execute(stmt)
    cap = res.scalars().first()
    if not cap:
        raise HTTPException(status_code=404, detail=f"Agent capability record '{agent_key}' not found.")
    
    cap.enabled = True
    await db.commit()

    # Log evolution event
    actor_email = identity.get("email") or identity.get("name") or "operator"
    await AgentLedgerReporter.log_capability_evolution(db, agent_key, "ENABLED", actor_email)
    
    return {"status": "success", "message": f"Agent '{agent_key}' has been enabled."}

@router.post("/capabilities/{agent_key}/disable", summary="Disable a registered agent")
async def disable_agent(
    agent_key: str,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.manage"))
):
    stmt = select(AgentCapabilityModel).where(AgentCapabilityModel.agent_key == agent_key)
    res = await db.execute(stmt)
    cap = res.scalars().first()
    if not cap:
        raise HTTPException(status_code=404, detail=f"Agent capability record '{agent_key}' not found.")
    
    cap.enabled = False
    await db.commit()

    # Log evolution event
    actor_email = identity.get("email") or identity.get("name") or "operator"
    await AgentLedgerReporter.log_capability_evolution(db, agent_key, "DISABLED", actor_email)

    return {"status": "success", "message": f"Agent '{agent_key}' has been disabled."}

@router.post("/runs", response_model=Dict[str, Any], summary="Execute an agent run in the sandbox")
async def execute_run(
    req: RunCreateRequest,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.manage"))
):
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    actor_email = identity.get("email") or identity.get("name") or "operator"
    
    success, output, workspace_path = await AgentSandboxExecutor.execute_run(
        db=db,
        run_id=run_id,
        agent_key=req.agent_key,
        command_handler=req.command_handler,
        arguments=req.arguments,
        target_paths=req.target_paths,
        cost=req.cost,
        network_domains=req.network_domains,
        created_by=actor_email
    )
    
    return {
        "run_id": run_id,
        "success": success,
        "output": output,
        "workspace_path": workspace_path
    }

@router.get("/runs", response_model=List[RunResponse], summary="List all agent execution runs")
async def list_runs(
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.read"))
):
    stmt = select(AgentRunModel).order_by(AgentRunModel.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/runs/{run_id}", response_model=RunResponse, summary="Get details of a specific agent run")
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.read"))
):
    stmt = select(AgentRunModel).where(AgentRunModel.run_id == run_id)
    res = await db.execute(stmt)
    run = res.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Agent run record '{run_id}' not found.")
    return run


# Promotion Pydantic Schemas
class PromotionCreateRequest(BaseModel):
    run_id: str = Field(..., example="run-12345")
    artifact_type: str = Field(..., example="patch")
    sandbox_artifact_path: str = Field(..., example="/tmp/agent-sandbox/workspace/patch.diff")
    target_repo_path: str = Field(..., example="apps/refine_control_plane/src/App.tsx")

class PromotionResponse(BaseModel):
    promotion_id: str
    run_id: str
    artifact_type: str
    sandbox_artifact_path: str
    target_repo_path: str
    artifact_hash: str
    manifest_hash: Optional[str] = None
    verified_artifact_hash: Optional[str] = None
    approved_artifact_hash: Optional[str] = None
    promoted_artifact_hash: Optional[str] = None
    target_path_hash: Optional[str] = None
    status: str
    verification_score: float
    verification_details: Dict[str, Any]
    approved_by: Optional[str] = None
    approved_at: Optional[Any] = None
    promoted_at: Optional[Any] = None
    ledger_event_hash: Optional[str] = None
    created_at: Any

    class Config:
        from_attributes = True

# Promotion Router Endpoints
@router.post("/promotions", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED, summary="Create a promotion request for an agent sandbox artifact")
async def create_promotion(
    req: PromotionCreateRequest,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.promotions.create"))
):
    actor = identity.get("email") or identity.get("name") or "operator"
    try:
        promo = await AgentPromotionGate.create_promotion_request(
            db=db,
            run_id=req.run_id,
            artifact_type=req.artifact_type,
            sandbox_artifact_path=req.sandbox_artifact_path,
            target_repo_path=req.target_repo_path,
            created_by=actor
        )
        return promo
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Promotion request creation failed: {e}")

@router.get("/promotions", response_model=List[PromotionResponse], summary="List all agent promotions")
async def list_promotions(
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.promotions.read"))
):
    stmt = select(AgentArtifactPromotionModel).order_by(AgentArtifactPromotionModel.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/promotions/{promotion_id}", response_model=PromotionResponse, summary="Get details of a specific promotion request")
async def get_promotion(
    promotion_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.promotions.read"))
):
    stmt = select(AgentArtifactPromotionModel).where(AgentArtifactPromotionModel.promotion_id == promotion_id)
    res = await db.execute(stmt)
    promo = res.scalars().first()
    if not promo:
        raise HTTPException(status_code=404, detail=f"Promotion request '{promotion_id}' not found.")
    return promo

@router.post("/promotions/{promotion_id}/approve", summary="Approve a verified promotion request")
async def approve_promotion(
    promotion_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.promotions.approve"))
):
    actor = identity.get("email") or identity.get("name") or "operator"
    try:
        await AgentPromotionGate.approve_promotion(db, promotion_id, actor)
        return {"status": "success", "message": f"Promotion request '{promotion_id}' approved."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approve failed: {e}")

@router.post("/promotions/{promotion_id}/reject", summary="Reject a promotion request")
async def reject_promotion(
    promotion_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.promotions.approve"))
):
    actor = identity.get("email") or identity.get("name") or "operator"
    try:
        await AgentPromotionGate.reject_promotion(db, promotion_id, actor)
        return {"status": "success", "message": f"Promotion request '{promotion_id}' rejected."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reject failed: {e}")

@router.post("/promotions/{promotion_id}/execute", summary="Execute and integrate approved promotion")
async def execute_promotion(
    promotion_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("agents.promotions.execute"))
):
    actor = identity.get("email") or identity.get("name") or "operator"
    try:
        success, msg = await AgentPromotionGate.execute_promotion(db, promotion_id, actor)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"status": "success", "message": msg}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {e}")
