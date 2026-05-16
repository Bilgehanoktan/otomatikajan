from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from libs.db.session import get_db
from services.ui_repair.schemas import (
    UISovereignIdentitySchema, UICapabilityTokenSchema, 
    UIAgentHandshakeSchema, HandshakeRequest, TokenIssueRequest,
    UIIdentityAuditEventSchema, UITrustScoreSchema
)
from services.ui_repair.sovereign_identity_registry import SovereignIdentityRegistry
from services.ui_repair.capability_token_service import CapabilityTokenService
from services.ui_repair.zero_trust_handshake import ZeroTrustHandshake
from services.ui_repair.trust_score_engine import TrustScoreEngine


router = APIRouter(prefix="/identity", tags=["Identity Governance"])

@router.get("/registry", response_model=List[UISovereignIdentitySchema])
async def get_identity_registry(db: AsyncSession = Depends(get_db)):
    registry = SovereignIdentityRegistry(db)
    return await registry.list_identities()

@router.post("/registry", response_model=UISovereignIdentitySchema)
async def register_identity(data: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    registry = SovereignIdentityRegistry(db)
    return await registry.register_identity(data)

@router.post("/tokens/issue", response_model=UICapabilityTokenSchema)
async def issue_capability_token(req: TokenIssueRequest, db: AsyncSession = Depends(get_db)):
    service = CapabilityTokenService(db)
    return await service.issue_token(
        identity_key=req.identity_key,
        scope=req.scope,
        actions=req.actions,
        duration_minutes=req.duration_minutes
    )

@router.post("/handshake", response_model=Dict[str, Any])
async def perform_handshake(req: HandshakeRequest, db: AsyncSession = Depends(get_db)):
    service = ZeroTrustHandshake(db)
    success, status, handshake = await service.verify_handshake(req.dict())
    
    if not success:
        # Record failed handshake in trust engine
        trust_engine = TrustScoreEngine(db)
        await trust_engine.record_event(req.source_identity_key, "FAILED_HANDSHAKE", success=False)
        raise HTTPException(status_code=403, detail=f"Handshake failed: {status}")
    
    return {"status": status, "handshake_id": str(handshake.id)}

@router.get("/trust-scores", response_model=List[UITrustScoreSchema])
async def get_trust_scores(db: AsyncSession = Depends(get_db)):
    from libs.db.models.ui_repair_models import UITrustScore
    from sqlalchemy import select
    res = await db.execute(select(UITrustScore))
    return list(res.scalars().all())

@router.get("/audit-events", response_model=List[UIIdentityAuditEventSchema])
async def get_identity_audit_events(db: AsyncSession = Depends(get_db)):
    from libs.db.models.ui_repair_models import UIIdentityAuditEvent
    from sqlalchemy import select
    res = await db.execute(select(UIIdentityAuditEvent).order_by(UIIdentityAuditEvent.created_at.desc()).limit(100))
    return list(res.scalars().all())

@router.post("/{identity_key}/revoke")
async def revoke_identity(identity_key: str, db: AsyncSession = Depends(get_db)):
    registry = SovereignIdentityRegistry(db)
    success = await registry.update_status(identity_key, "REVOKED")
    if not success:
        raise HTTPException(status_code=404, detail="Identity not found")
    return {"status": "REVOKED"}
