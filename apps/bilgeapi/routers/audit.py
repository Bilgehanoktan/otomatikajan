from typing import List
from fastapi import APIRouter, Depends, Query
from apps.bilgeapi.schemas.audit import AuditEvent
from apps.bilgeapi.repositories.interface import AuditRepository
from apps.bilgeapi.routers.deps import get_audit_repository
from apps.bilgeapi.auth import require_permission

router = APIRouter(prefix="/v1")

@router.get("/audit-events", response_model=List[AuditEvent], tags=["Audit"])
async def list_audit_events(
    limit: int = Query(50, ge=1, le=500),
    audit_repo: AuditRepository = Depends(get_audit_repository),
    _identity: dict = Depends(require_permission("bilgeapi.audit.read"))
):
    tenant_id = _identity.get("tenant_id") or "default"
    return await audit_repo.list_recent(tenant_id=tenant_id, limit=limit)

