from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.repositories.interface import (
    RemediationRunbookRepository,
    RemediationAttemptRepository
)
from apps.bilgeapi.routers.deps import (
    get_remediation_runbook_repository,
    get_remediation_attempt_repository,
    get_self_healing_executor,
    get_emergency_recovery_service,
)
from apps.bilgeapi.schemas.self_healing import (
    RemediationAttemptResponse,
    RemediationRunbookResponse,
    EmergencyRecoveryRequest,
)

router = APIRouter(prefix="/v1/watchdog", tags=["System Watchdog Self-Healing"])


class RemediateRequest(BaseModel):
    runbook_id: str


@router.get("/remediations", response_model=List[RemediationAttemptResponse])
async def list_remediation_attempts(
    finding_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: RemediationAttemptRepository = Depends(get_remediation_attempt_repository),
):
    if finding_id:
        return await repo.list_attempts_by_finding(finding_id)
    return await repo.list_attempts(limit=limit)


@router.get("/remediations/{attempt_id}", response_model=RemediationAttemptResponse)
async def get_remediation_attempt(
    attempt_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: RemediationAttemptRepository = Depends(get_remediation_attempt_repository),
):
    attempt = await repo.get_attempt(attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Remediation attempt not found")
    return attempt


@router.post("/findings/{finding_id}/remediate", response_model=RemediationAttemptResponse)
async def trigger_remediation(
    finding_id: str,
    req: RemediateRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    executor: Any = Depends(get_self_healing_executor),
):
    try:
        actor_id = identity.get("id", "admin")
        return await executor.execute_remediation(finding_id, req.runbook_id, actor_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runbooks", response_model=List[RemediationRunbookResponse])
async def list_runbooks(
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: RemediationRunbookRepository = Depends(get_remediation_runbook_repository),
):
    return await repo.list_runbooks()


@router.post("/runbooks/{runbook_id}/enable", response_model=RemediationRunbookResponse)
async def enable_runbook(
    runbook_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.admin")),
    repo: RemediationRunbookRepository = Depends(get_remediation_runbook_repository),
):
    runbook = await repo.update_runbook_enabled(runbook_id, True)
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return runbook


@router.post("/runbooks/{runbook_id}/disable", response_model=RemediationRunbookResponse)
async def disable_runbook(
    runbook_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.admin")),
    repo: RemediationRunbookRepository = Depends(get_remediation_runbook_repository),
):
    runbook = await repo.update_runbook_enabled(runbook_id, False)
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return runbook


@router.post("/emergency-recovery/run", response_model=RemediationAttemptResponse)
async def run_emergency_recovery(
    req: EmergencyRecoveryRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    recovery_service: Any = Depends(get_emergency_recovery_service),
):
    try:
        actor_id = identity.get("id", "admin")
        return await recovery_service.run_emergency_recovery(
            finding_id=req.finding_id,
            action_type=req.action_type,
            actor_id=actor_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
