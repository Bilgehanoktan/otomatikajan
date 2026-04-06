from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Optional, Any
from pydantic import BaseModel

from apps.api.routers.auth.jwt_auth import get_current_user, require_admin
from apps.worker.tasks.celery_app import celery_app  # type: ignore
from packages.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator as orchestrator
from packages.persistence.session import AsyncSessionLocal, get_db_dep
from packages.improvement_engine.cognitive_verifier import cognitive_verifier
from packages.orchestration.agi.cognitive.sovereign_auditor import sovereign_auditor
from packages.orchestration.agi.cognitive.evolution_engine import evolution_engine
from packages.persistence.models import User
from packages.observability.logging import get_logger

router = APIRouter(prefix="/improvements", tags=["Self-Improvement"])
logger = get_logger("api.improvement")


class ScanRequest(BaseModel):
    limit: Optional[int] = 10
    auto_apply: Optional[bool] = False


class ImprovementResponse(BaseModel):
    id: str
    description: str
    severity: str
    affected_files: List[str]
    evidence: dict


class ApplyPatchRequest(BaseModel):
    target_path: str
    instruction: str


@router.get("/scan", response_model=List[ImprovementResponse])
async def scan_for_improvements(background_tasks: BackgroundTasks, current_user=Depends(get_current_user)):
    try:
        proposals: List[Any] = await evolution_engine.get_active_proposals()
        
        # EÄŸer aktif Ã¶neri yoksa, bir dÃ¶ngÃ¼ tetikle (Arka planda)
        if not proposals:
            background_tasks.add_task(evolution_engine.run_evolution_cycle)
            return []

        return [
            ImprovementResponse(
                id=p["id"],
                description=p["finding"]["title"],
                severity=p["finding"].get("severity", "medium"),
                affected_files=[p["finding"].get("evidence", {}).get("affected_file", "system")],
                evidence={
                    "finding": p["finding"],
                    "patch": p.get("patch"),
                    "reasoning": p.get("reasoning")
                }
            )
            for p in proposals
        ]
    except Exception as e:
        logger.error(f"Improvement scan hatasÄ±: {e}")
        raise HTTPException(status_code=500, detail=f"Scan baÅŸarÄ±sÄ±z: {e}")


@router.post("/apply-proposal/{proposal_id}")
async def apply_autonomous_proposal(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_admin),
):
    try:
        proposals = await evolution_engine.get_active_proposals()
        proposal = next((p for p in proposals if p["id"] == proposal_id), None)
        
        if not proposal:
            raise HTTPException(status_code=404, detail=f"Ä°yileÅŸtirme ID {proposal_id} bulunamadÄ±.")

        background_tasks.add_task(evolution_engine.apply_evolution, proposal)
        return {"status": "started", "message": f"Evrim adÄ±mÄ± {proposal_id} uygulanmaya baÅŸlandÄ±."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proposal uygulama hatasÄ±: {e}")
        raise HTTPException(status_code=500, detail=f"Sistem hatasÄ±: {str(e)}")

@router.post("/apply-patch")
async def apply_custom_patch(
    request: ApplyPatchRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_admin),
):
    if not orchestrator.self_updater:
        raise HTTPException(status_code=503, detail="Self-Updater modÃ¼lÃ¼ yÃ¼klenmemiÅŸ.")

    background_tasks.add_task(
        orchestrator.self_updater.modify_system_file,
        target_file_path=request.target_path,
        instruction=request.instruction,
    )

    return {
        "status": "started",
        "target": request.target_path,
        "message": "Patch iÅŸlemi arka planda baÅŸlatÄ±ldÄ±.",
    }


@router.get("/history")
async def get_improvement_history(limit: int = 50, current_user=Depends(get_current_user)):
    if not orchestrator.self_updater:
        return {"updates": []}

    updates = orchestrator.self_updater.registry.get_recent_updates(limit=limit)
    return {"updates": updates}


@router.get("/state")
async def get_improvement_state(current_user=Depends(get_current_user)):
    return {
        "observer_active": True,
        "self_updater_active": orchestrator.self_updater is not None,
        "is_autonomous": False,
        "high_risk_paths": list(getattr(orchestrator.self_updater, "HIGH_RISK_PATHS", [])),
    }

