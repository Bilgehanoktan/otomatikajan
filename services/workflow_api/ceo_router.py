from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.session import get_db
from services.auth.jwt_auth import require_permission
from services.orchestration.ceo.repair_bridge import (
    ExternalRepairRequest,
    build_repair_case_from_finding,
    start_self_repair_from_repair_case,
)

from services.repair.ui_diagnostics import UIDiagnosticRequest
from services.repair.stagehand_adapter import (
    run_stagehand_diagnostic,
    write_diagnostic_artifact,
    map_diagnostic_to_ceo_finding,
)

router = APIRouter(tags=["CEO Findings Bridge"])

@router.post("/findings/{finding_id}/repair-case")
async def create_repair_case_from_ceo_finding(
    finding_id: str,
    body: ExternalRepairRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
    db: AsyncSession = Depends(get_db),
):
    """
    Bridges a CEO dashboard finding or recommendation to the self-repair pipeline.
    Validates identity permissions, maps finding fields, generates repair_case.json,
    and returns a structured transition payload.
    """
    if body.finding.finding_id != finding_id:
        raise HTTPException(
            status_code=400,
            detail=f"Mismatched finding_id: path has '{finding_id}' but payload has '{body.finding.finding_id}'"
        )

    try:
        # 1. Build and serialize the repair case
        result = build_repair_case_from_finding(body.finding)
        
        # 2. Trigger TaskFlow bridge according to auto_start policy
        trigger_res = await start_self_repair_from_repair_case(result.case_input, auto_start=body.auto_start, db=db)
        
        # 3. Formulate compliant response
        return {
            "status": "created",
            "finding_id": result.finding_id,
            "repair_case_id": result.repair_case_id,
            "incident_id": result.incident_id,
            "artifact_ref": result.artifact_ref,
            "recommended_agent": result.recommended_agent,
            "requested_mode": result.requested_mode,
            "next_step": "start_self_repair_taskflow" if not body.auto_start else "taskflow_running",
            "trigger_status": trigger_res
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bridge CEO finding to repair case: {e}")


@router.post("/diagnostics/stagehand")
async def post_stagehand_diagnostic(
    body: UIDiagnosticRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Runs a UI diagnostic using the Stagehand adapter and translates the diagnostic results into a standard CEO Finding payload.
    """
    try:
        # 1. Run the Stagehand diagnostic
        result = run_stagehand_diagnostic(body)
        
        # 2. Persist diagnostic artifacts (diagnostic_report.json, network/console logs)
        write_diagnostic_artifact(result)
        
        # 3. Map result to CEOFindingPayload
        finding = map_diagnostic_to_ceo_finding(result)
        
        artifact_ref = f"repair_outputs/diagnostics/{result.diagnostic_id}/diagnostic_report.json"
        
        return {
            "status": "created",
            "diagnostic_id": result.diagnostic_id,
            "artifact_ref": artifact_ref,
            "finding": finding,
            "next_step": "create_repair_case"
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic run failed: {e}")
