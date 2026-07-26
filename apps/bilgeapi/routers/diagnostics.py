from typing import List
from fastapi import APIRouter, Depends, HTTPException
from apps.bilgeapi.schemas.diagnostic import DiagnosticStartResponse, DiagnosticResult
from apps.bilgeapi.repositories.interface import DiagnosticRepository
from apps.bilgeapi.services.diagnostic import DiagnosticService
from apps.bilgeapi.routers.deps import get_diagnostic_repository, get_diagnostic_service
from apps.bilgeapi.auth import require_permission

router = APIRouter(prefix="/v1")

@router.post("/incidents/{incident_id}/diagnostics", response_model=DiagnosticStartResponse, status_code=202, tags=["Diagnostics"])
async def trigger_diagnostic(
    incident_id: str,
    diag_service: DiagnosticService = Depends(get_diagnostic_service),
    _identity: dict = Depends(require_permission("bilgeapi.diagnostic.run"))
):
    run = await diag_service.start_diagnostic(incident_id)
    if not run:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    return DiagnosticStartResponse(
        diagnostic_id=run.diagnostic_id,
        status=run.status,
        next_action="CHECK_DIAGNOSTIC_STATUS"
    )

@router.get("/diagnostics", response_model=List[DiagnosticResult], tags=["Diagnostics"])
async def list_diagnostics(
    diag_repo: DiagnosticRepository = Depends(get_diagnostic_repository),
    _identity: dict = Depends(require_permission("bilgeapi.incident.read"))
):
    return await diag_repo.list_all()

@router.get("/diagnostics/{diagnostic_id}", response_model=DiagnosticResult, tags=["Diagnostics"])
async def get_diagnostic(
    diagnostic_id: str,
    diag_repo: DiagnosticRepository = Depends(get_diagnostic_repository),
    _identity: dict = Depends(require_permission("bilgeapi.incident.read"))
):
    diag = await diag_repo.get(diagnostic_id)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnostic run not found")
    return diag

