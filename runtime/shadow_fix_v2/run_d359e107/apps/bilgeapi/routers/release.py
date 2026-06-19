import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException

from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.routers.deps import get_release_gate_service
from apps.bilgeapi.schemas.release import ReleaseCheckCreate, ReleaseCheckResponse
from apps.bilgeapi.services.release import BilgeAPIReleaseGate

logger = logging.getLogger("bilgeapi.release_router")

router = APIRouter(prefix="/v1/release", tags=["Release Gate"])

@router.post("/readiness", response_model=ReleaseCheckResponse)
async def run_readiness_check(
    request: Request,
    body: ReleaseCheckCreate,
    service: BilgeAPIReleaseGate = Depends(get_release_gate_service),
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Executes a new release readiness audit, including E2E smoke tests and security hardening checks.
    Persists results to database.
    """
    check_data = await service.execute_readiness_audit(triggered_by=body.triggered_by)
    # Dynamically audit registered endpoints using the active FastAPI app instance
    endpoints_res = service.check_endpoints(request.app)
    check_data["checked_endpoints"] = endpoints_res

    # Check for endpoint check errors/missing to include in blockers
    missing_endpoints = [ep for ep, stat in endpoints_res.items() if stat == "MISSING"]
    if missing_endpoints:
        check_data["blockers"].append(f"Crucial endpoint check failed: {', '.join(missing_endpoints)}")
        check_data["status"] = "BLOCKED"
        # Recalculate score with blockers penalty
        score = 100.0 - len(check_data["warnings"]) * 5.0 - len(check_data["blockers"]) * 20.0
        check_data["score"] = max(0.0, score)

    persisted = await service.repo.create_check(check_data)
    return persisted

@router.get("/readiness", response_model=List[ReleaseCheckResponse])
async def list_readiness_checks(
    limit: int = Query(20, ge=1, le=100),
    service: BilgeAPIReleaseGate = Depends(get_release_gate_service),
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Lists historical release readiness checks from database (newest first).
    """
    checks = await service.repo.list_checks(limit=limit)
    return checks

@router.get("/readiness/latest", response_model=ReleaseCheckResponse)
async def get_latest_readiness_check(
    service: BilgeAPIReleaseGate = Depends(get_release_gate_service),
    identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Returns the single most recent release readiness check from database.
    """
    check = await service.repo.get_latest_check()
    if not check:
        raise HTTPException(status_code=404, detail="No release check has been recorded yet.")
    return check
