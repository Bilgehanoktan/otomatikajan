from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.routers.deps import (
    get_review_ledger_repository,
    get_review_ledger_service,
    get_review_ledger_verifier,
)
from apps.bilgeapi.repositories.interface import ReviewLedgerRepository
from apps.bilgeapi.schemas.review_ledger import (
    ReviewLedgerAppendRequest,
    ReviewLedgerChainResponse,
    ReviewLedgerEntryResponse,
    ReviewLedgerExportResponse,
    ReviewLedgerVerifyResponse,
)

router = APIRouter(prefix="/v1/review-ledger", tags=["Review Ledger"])


@router.get("/recent", response_model=List[ReviewLedgerEntryResponse])
async def list_recent_ledger_entries(
    limit: int = Query(default=25, ge=1, le=100),
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: ReviewLedgerRepository = Depends(get_review_ledger_repository),
):
    tenant_id = _identity.get("tenant_id")
    return await repo.list_recent(tenant_id=tenant_id, limit=limit)


@router.get("/chains/{chain_id}", response_model=ReviewLedgerChainResponse)
async def get_ledger_chain(
    chain_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    service: Any = Depends(get_review_ledger_service),
):
    tenant_id = _identity.get("tenant_id")
    entries = await service.list_chain(chain_id, tenant_id=tenant_id)
    return {"chain_id": chain_id, "entries": entries}


@router.get("/chains/{chain_id}/verify", response_model=ReviewLedgerVerifyResponse)
async def verify_ledger_chain(
    chain_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    verifier: Any = Depends(get_review_ledger_verifier),
):
    tenant_id = _identity.get("tenant_id")
    return await verifier.verify_chain(chain_id, tenant_id=tenant_id)


@router.get("/chains/{chain_id}/export", response_model=ReviewLedgerExportResponse)
async def export_ledger_chain(
    chain_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_review_ledger_service),
    verifier: Any = Depends(get_review_ledger_verifier),
):
    tenant_id = _identity.get("tenant_id")
    verification = await verifier.verify_chain(chain_id, tenant_id=tenant_id)
    content = await service.export_chain_markdown(chain_id, verification, tenant_id=tenant_id)
    return {
        "chain_id": chain_id,
        "format": "markdown",
        "valid": verification["valid"],
        "entry_count": verification["entry_count"],
        "content": content,
    }


@router.post("/events", response_model=ReviewLedgerEntryResponse, status_code=status.HTTP_201_CREATED)
async def append_ledger_event(
    body: ReviewLedgerAppendRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_review_ledger_service),
):
    actor_id = body.actor_id or identity.get("id", "admin")
    tenant_id = identity.get("tenant_id")
    if not body.chain_id.strip():
        raise HTTPException(status_code=400, detail="chain_id is required")
    return await service.append_event(
        chain_id=body.chain_id,
        event_type=body.event_type,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        actor_id=actor_id,
        payload=body.payload,
        tenant_id=tenant_id,
    )
