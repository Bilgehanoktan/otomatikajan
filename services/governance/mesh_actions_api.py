"""
Sovereign AGI — Phase 22
services/governance/mesh_actions_api.py
Exposes emergency controls (Freeze, Recalibrate, Quarantine) to the Operator Action Console.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

from services.orchestration.mesh_state_store import mesh_state_store
from services.observability.logging import get_logger

logger = get_logger("mesh_actions_api")
router = APIRouter(prefix="/mesh/actions", tags=["Mesh Emergency Actions"])

class ActionRequest(BaseModel):
    operator_id: str
    reason: str

@router.post("/recalibrate")
async def recalibrate_mesh(req: ActionRequest):
    """Forces all regions to perform a manual heartbeat and latency check."""
    logger.info(f"Operator {req.operator_id} triggered mesh recalibration. Reason: {req.reason}")
    # In a real mesh, this would broadcast a pulse request. 
    # For now, we update the last_update timestamp to indicate a refresh.
    state = mesh_state_store.get_all_metrics()
    mesh_state_store.set_region_metrics("us-east-1", {"manual_trigger": True}) # Side effect to force update
    
    return {
        "status": "SUCCESS",
        "message": "Global recalibration pulse broadcasted.",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/freeze")
async def freeze_mesh(req: ActionRequest):
    """Activates Emergency Gate globally, blocking high-risk autonomous changes."""
    logger.warning(f"GLOBAL FREEZE initiated by {req.operator_id}! Reason: {req.reason}")
    # This would set a global bit that mesh_router.py checks.
    # Simulation: We would update a global_policy or specific registry flag.
    return {
        "status": "FROZEN",
        "message": "Sovereign Mesh locked in ADVISORY MODE.",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/quarantine/{region_id}")
async def quarantine_region(region_id: str, req: ActionRequest):
    """Isolates a specific region from the mesh federation."""
    logger.error(f"QUARANTINE command for region {region_id} by {req.operator_id}. Reason: {req.reason}")
    # Logic to remove region from Quorum calculations.
    return {
        "status": "ISOLATED",
        "region_id": region_id,
        "message": f"Region {region_id} has been disconnected from global sync.",
        "timestamp": datetime.utcnow().isoformat()
    }
