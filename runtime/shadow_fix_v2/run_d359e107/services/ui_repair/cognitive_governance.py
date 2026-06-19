import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.session import get_db
from libs.db.models.ui_repair_models import (
    UICognitiveIntegrityCheck,
    UILLMClaim,
    UIHallucinationFinding,
    UISemanticDriftEvent,
    UICognitiveStatus,
    UICognitiveDecision,
    UICognitiveOutputType
)
from services.ui_repair.schemas import (
    UICognitiveIntegrityCheckSchema,
    UILLMClaimSchema,
    UIHallucinationFindingSchema,
    UISemanticDriftEventSchema,
    CognitiveCheckRequest
)
from services.ui_repair.cognitive_integrity_guard import CognitiveIntegrityGuard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cognitive", tags=["Cognitive Integrity"])

@router.get("/checks", response_model=List[UICognitiveIntegrityCheckSchema])
async def get_checks(
    status: str | None = None,
    agent_name: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UICognitiveIntegrityCheck)
    if status:
        stmt = stmt.where(UICognitiveIntegrityCheck.status == status)
    if agent_name:
        stmt = stmt.where(UICognitiveIntegrityCheck.agent_name == agent_name)
    
    res = await db.execute(stmt.order_by(UICognitiveIntegrityCheck.created_at.desc()).limit(100))
    return res.scalars().all()

@router.post("/check", response_model=UICognitiveIntegrityCheckSchema)
async def trigger_check(request: CognitiveCheckRequest, db: AsyncSession = Depends(get_db)):
    guard = CognitiveIntegrityGuard(db)
    try:
        output_type = UICognitiveOutputType(request.output_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid output type: {request.output_type}")
        
    check = await guard.run_check(
        source_type=request.source_type,
        source_id=request.source_id,
        agent_name=request.agent_name,
        output_type=output_type,
        content=request.content,
        expected_context=request.context_data
    )
    return check

@router.get("/findings/{check_id}", response_model=List[UIHallucinationFindingSchema])
async def get_findings(check_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(UIHallucinationFinding).where(UIHallucinationFinding.check_id == check_id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/claims/{check_id}", response_model=List[UILLMClaimSchema])
async def get_claims(check_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(UILLMClaim).where(UILLMClaim.check_id == check_id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/drift-events", response_model=List[UISemanticDriftEventSchema])
async def get_drift_events(db: AsyncSession = Depends(get_db)):
    stmt = select(UISemanticDriftEvent).order_by(UISemanticDriftEvent.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/manual-review", response_model=List[UICognitiveIntegrityCheckSchema])
async def get_manual_review_queue(db: AsyncSession = Depends(get_db)):
    stmt = select(UICognitiveIntegrityCheck).where(
        UICognitiveIntegrityCheck.status == UICognitiveStatus.MANUAL_REVIEW_REQUIRED
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/manual-review/{check_id}/approve")
async def approve_check(check_id: str, rationale: str = Query(...), db: AsyncSession = Depends(get_db)):
    stmt = select(UICognitiveIntegrityCheck).where(UICognitiveIntegrityCheck.id == check_id)
    res = await db.execute(stmt)
    check = res.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    
    check.status = UICognitiveStatus.PASSED
    check.decision = UICognitiveDecision.ALLOW
    check.reason = f"Operator Approved: {rationale}"
    await db.commit()
    return {"status": "approved"}

@router.post("/manual-review/{check_id}/reject")
async def reject_check(check_id: str, rationale: str = Query(...), db: AsyncSession = Depends(get_db)):
    stmt = select(UICognitiveIntegrityCheck).where(UICognitiveIntegrityCheck.id == check_id)
    res = await db.execute(stmt)
    check = res.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    
    check.status = UICognitiveStatus.BLOCKED
    check.decision = UICognitiveDecision.BLOCK_ACTION
    check.reason = f"Operator Rejected: {rationale}"
    await db.commit()
    return {"status": "rejected"}
