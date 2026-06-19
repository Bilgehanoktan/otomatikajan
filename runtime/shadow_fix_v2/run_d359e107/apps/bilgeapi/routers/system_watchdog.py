from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.repositories.interface import SystemFindingRepository
from apps.bilgeapi.routers.deps import (
    get_system_finding_repository,
    get_system_finding_service,
    get_system_watchdog_service,
)
from apps.bilgeapi.schemas.system_watchdog import (
    SystemFindingResponse,
    WatchdogRunResponse,
    WatchdogStatusResponse,
)


router = APIRouter(prefix="/v1/watchdog", tags=["System Watchdog"])


@router.post("/run", response_model=WatchdogRunResponse, status_code=status.HTTP_200_OK)
async def run_watchdog_scan(
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_system_watchdog_service),
):
    try:
        return await service.run_scan(actor_id=identity.get("id", "admin"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status", response_model=WatchdogStatusResponse)
async def get_watchdog_status(
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    service: Any = Depends(get_system_watchdog_service),
    repo: SystemFindingRepository = Depends(get_system_finding_repository),
):
    return await service.status(repo)


@router.get("/findings", response_model=List[SystemFindingResponse])
async def list_watchdog_findings(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    severity: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: SystemFindingRepository = Depends(get_system_finding_repository),
):
    return await repo.list_findings(status=status_filter, severity=severity, limit=limit)


@router.get("/findings/{finding_id}", response_model=SystemFindingResponse)
async def get_watchdog_finding(
    finding_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: SystemFindingRepository = Depends(get_system_finding_repository),
):
    finding = await repo.get_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="System finding not found")
    return finding


@router.post("/findings/{finding_id}/acknowledge", response_model=SystemFindingResponse)
async def acknowledge_watchdog_finding(
    finding_id: str,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_system_finding_service),
):
    try:
        return await service.acknowledge(finding_id, identity.get("id", "admin"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/findings/{finding_id}/dismiss", response_model=SystemFindingResponse)
async def dismiss_watchdog_finding(
    finding_id: str,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_system_finding_service),
):
    try:
        return await service.dismiss(finding_id, identity.get("id", "admin"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
