from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
import uuid

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
    get_system_finding_service,
    get_review_ledger_service,
)
from apps.bilgeapi.schemas.self_healing import (
    RemediationAttemptResponse,
    RemediationRunbookResponse,
    EmergencyRecoveryRequest,
    FindingIntakeRequest,
    ExternalRecoveryReportRequest,
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


@router.post("/findings/intake", response_model=Dict[str, Any])
async def intake_finding(
    req: FindingIntakeRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    finding_service: Any = Depends(get_system_finding_service),
):
    try:
        actor_id = identity.get("id", "admin")
        sev_map = {
            "CRITICAL": 85.0,
            "HIGH": 65.0,
            "MEDIUM": 35.0,
            "LOW": 15.0
        }
        risk_score = sev_map.get(req.severity.upper(), 15.0)
        
        scored_signal = {
            "source_type": req.source_type,
            "source_id": req.source_id,
            "title": req.title,
            "description": req.description,
            "risk_score": risk_score,
            "severity": req.severity.upper(),
            "evidence": req.evidence_summary or {},
            "recommended_action": req.recommended_action,
            "tenant_id": req.tenant_id,
            "links": {}
        }
        
        correlation_id = f"intake_{uuid.uuid4().hex[:12]}"
        
        result = await finding_service.find_or_create_from_signal(
            scored_signal=scored_signal,
            actor_id=actor_id,
            correlation_id=correlation_id
        )
        return {
            "status": "success",
            "finding_id": result["finding"]["id"],
            "created": result.get("created", False),
            "deduped": result.get("deduped", False),
            "terminal": result.get("terminal", False)
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/external-recovery/report", status_code=status.HTTP_200_OK)
async def report_external_recovery(
    req: ExternalRecoveryReportRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    ledger_service: Any = Depends(get_review_ledger_service),
):
    try:
        actor_id = identity.get("id", "admin")
        for event in req.events:
            redacted_payload = {
                "service_name": event.service_name,
                "attempt_no": event.attempt_no,
                "status": event.status,
                "timestamp": event.timestamp,
                "output_redacted": (event.output[:200] + "...") if event.output else None,
                "error_redacted": (event.error[:200] + "...") if event.error else None,
            }
            await ledger_service.append_event(
                chain_id="external-recovery-supervisor",
                event_type=event.event_type.upper(),
                entity_type="supervisor_event",
                entity_id=f"rec_{event.timestamp}_{event.service_name}",
                actor_id=actor_id,
                payload=redacted_payload,
            )
        return {"status": "success", "processed_events": len(req.events)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

