"""
Sovereign AGI — Phase 31
services/governance/learning_api.py
API endpoints for the Learning Engine (Fingerprints, Records, Strategy Memory).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid

from libs.db.session import get_db
from services.governance.learning_repository import LearningRepository
from services.auth.jwt_auth import require_permission

router = APIRouter(prefix="/learning", tags=["Autonomous Learning"])

@router.get("/fingerprints")
async def list_fingerprints(
    limit: int = 50, 
    offset: int = 0, 
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("learning.view"))
):
    repo = LearningRepository(db)
    return await repo.get_fingerprints(limit, offset)

@router.get("/fingerprints/{id}")
async def get_fingerprint_detail(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("learning.view"))
):
    repo = LearningRepository(db)
    detail = await repo.get_fingerprint_detail(id)
    if not detail:
        raise HTTPException(status_code=404, detail="Fingerprint not found")
    return detail

@router.get("/records")
async def list_learning_records(
    limit: int = 50, 
    offset: int = 0, 
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("learning.view"))
):
    repo = LearningRepository(db)
    return await repo.get_learning_records(limit, offset)

@router.get("/strategy-memory")
async def list_strategy_memory(
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("learning.view"))
):
    repo = LearningRepository(db)
    return await repo.get_strategy_memory()

@router.get("/negative-patterns")
async def list_negative_patterns(
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("learning.view"))
):
    repo = LearningRepository(db)
    return await repo.get_negative_patterns()

@router.get("/adaptation-candidates")
async def list_adaptation_candidates(
    db: AsyncSession = Depends(get_db),
    identity: Dict[str, Any] = Depends(require_permission("learning.view"))
):
    repo = LearningRepository(db)
    return await repo.get_adaptation_candidates()

@router.post("/scan-proposals")
async def scan_for_proposals(
    identity: Dict[str, Any] = Depends(require_permission("learning.trigger"))
):
    """Triggers an autonomous scan for policy evolution candidates."""
    from services.governance.policy.policy_proposal_engine import PolicyProposalEngine
    proposals = await PolicyProposalEngine.generate_proposals()
    
    return {
        "status": "SUCCESS",
        "scan_time": str(datetime.now(timezone.utc)),
        "candidates_found": len(proposals),
        "proposals": proposals
    }

@router.get("/global-stats")
async def get_global_learning_stats(
    identity: Dict[str, Any] = Depends(require_permission("learning.view"))
):
    """Returns system-wide aggregated learning metrics."""
    from services.governance.learning_orchestrator import LearningOrchestrator
    return await LearningOrchestrator.get_global_learning_stats()
