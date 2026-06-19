from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.schemas.api_key import (
    ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse, ApiKeyRevoke,
    ApiKeyQuotaUpdate, ApiKeyQuotaUsageResponse
)
from apps.bilgeapi.services.api_key import ApiKeyService
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.services.quota import get_quota_service_instance
from apps.bilgeapi.routers.deps import get_api_key_service, get_audit_service

router = APIRouter(prefix="/v1/admin/api-keys", tags=["API Keys"])

@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreate,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """Create a new database-backed API key. Plaintext key is returned only once."""
    actor_id = identity.get("id", "system")
    new_key = await service.generate_api_key(
        role=body.role,
        description=body.description,
        tenant_id=body.tenant_id,
        expires_in_days=body.expires_in_days,
        actor_id=actor_id,
        quota_daily=body.quota_daily,
        quota_monthly=body.quota_monthly
    )
    return new_key

@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    _identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """List all API keys (metadata only, plaintext key is never returned)."""
    return await service.list_keys()

@router.get("/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """Retrieve metadata of a single API key."""
    key = await service.get_key(key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key

@router.post("/{key_id}/revoke", response_model=ApiKeyResponse)
async def revoke_api_key(
    key_id: str,
    body: ApiKeyRevoke,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: ApiKeyService = Depends(get_api_key_service)
):
    """Revoke a dynamic API key immediately."""
    actor_id = identity.get("id", "system")
    key = await service.revoke_api_key(key_id, actor_id=actor_id, reason=body.reason)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key

@router.put("/{key_id}/quota", response_model=ApiKeyResponse)
async def update_api_key_quota(
    key_id: str,
    body: ApiKeyQuotaUpdate,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: ApiKeyService = Depends(get_api_key_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Update daily and monthly quota limits for a specific API key."""
    updated = await service.update_quota(
        key_id=key_id,
        quota_daily=body.quota_daily,
        quota_monthly=body.quota_monthly,
        actor_id=identity.get("id", "system")
    )
    if not updated:
        raise HTTPException(status_code=404, detail="API key not found")
    return updated

@router.get("/{key_id}/quota-usage", response_model=ApiKeyQuotaUsageResponse)
async def get_api_key_quota_usage(
    key_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: ApiKeyService = Depends(get_api_key_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Get current quota usage statistics for a specific API key."""
    key = await service.get_key(key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    quota_daily = key.get("quota_daily")
    quota_monthly = key.get("quota_monthly")

    quota_svc = get_quota_service_instance(audit_service)
    daily_used, monthly_used = quota_svc.get_usage_from_redis(key_id)

    daily_remaining = None
    if quota_daily is not None:
        daily_remaining = max(0, quota_daily - daily_used)

    monthly_remaining = None
    if quota_monthly is not None:
        monthly_remaining = max(0, quota_monthly - monthly_used)

    return ApiKeyQuotaUsageResponse(
        key_id=key_id,
        quota_daily=quota_daily,
        quota_monthly=quota_monthly,
        daily_used=daily_used,
        monthly_used=monthly_used,
        daily_remaining=daily_remaining,
        monthly_remaining=monthly_remaining
    )
