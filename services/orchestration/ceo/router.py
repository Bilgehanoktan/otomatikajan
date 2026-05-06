"""
CEO Engine API — Phase 12.1
Exposes strategic findings, manual task approval, and on-demand scanning.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict, List
import uuid
import logging

from libs.db.session import get_db
from services.auth.jwt_auth import require_permission
from services.orchestration.ceo.engine import CEOEngine
from libs.llm.model_orchestrator import model_orchestrator

router = APIRouter(tags=["CEO Engine"])
logger = logging.getLogger("services.orchestration.ceo.router")

# Singleton CEO Engine
ceo_engine = CEOEngine(model_orch=model_orchestrator)

@router.get("/overview")
async def get_ceo_overview(
    identity: Dict[str, Any] = Depends(require_permission("governor.view"))
):
    """Returns strategic findings, suggestions, and health metrics."""
    try:
        return await ceo_engine.get_overview()
    except Exception as e:
        logger.exception("Failed to get CEO overview")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan")
async def trigger_ceo_scan(
    identity: Dict[str, Any] = Depends(require_permission("governor.scan"))
):
    """Triggers an on-demand strategic scan of the system."""
    try:
        findings = await ceo_engine.run_scan()
        return {"status": "success", "findings_count": len(findings) if findings else 0}
    except Exception as e:
        logger.exception("CEO Scan failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve/{suggestion_id}")
async def approve_ceo_suggestion(
    suggestion_id: str,
    identity: Dict[str, Any] = Depends(require_permission("governor.execute"))
):
    """Manually approves a CEO suggestion and creates a project."""
    try:
        uid = uuid.UUID(suggestion_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid suggestion ID format")
        
    try:
        result = await ceo_engine.manual_approve_suggestion(uid)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Approval failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"CEO Approval failed for {suggestion_id}")
        raise HTTPException(status_code=500, detail=str(e))
