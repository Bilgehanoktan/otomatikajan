from fastapi import APIRouter, Depends, Response
from typing import List, Dict, Any
from pydantic import BaseModel
from services.auth.jwt_auth import require_permission
from services.workflow_api.governance_router import AuditBundleCreate

router = APIRouter(tags=["Compatibility & Stubs"])

@router.get("/federation")
async def list_federation_stub(): return []

@router.get("/safety")
async def list_safety_stub(): return []

@router.get("/training")
async def list_training_stub(): return []

@router.get("/costs")
async def list_costs_stub(): return []

@router.get("/audit")
async def list_audit_stub(): return []

@router.get("/audit-bundles")
@router.get("/audit-bundles/")
@router.get("/compliance/audit-bundles")
@router.get("/compliance/audit-bundles/")
async def list_audit_bundles_compat(response: Response):
    from services.workflow_api.governance_router import list_audit_bundles
    return await list_audit_bundles(response)

@router.post("/audit-bundles")
@router.post("/audit-bundles/")
@router.post("/compliance/audit-bundles")
@router.post("/compliance/audit-bundles/")
async def create_audit_bundle_compat(
    req: AuditBundleCreate,
    identity: Dict[str, Any] = Depends(require_permission("audit.create"))
):
    from services.workflow_api.governance_router import create_audit_bundle_endpoint
    return await create_audit_bundle_endpoint(req, identity)

@router.get("/mesh")
async def list_mesh_stub(): return []

@router.post("/ops/handover")
@router.post("/ops/handover/")
async def handover_compat(
    project_id: str,
    dry_run: bool = True,
    identity: Dict[str, Any] = Depends(require_permission("ops.handover"))
):
    from services.workflow_api.governance_router import trigger_handover
    return await trigger_handover(project_id, dry_run, identity)

@router.get("/verifiers")
async def list_verifiers_stub(): return []

@router.get("/governance-lineage")
async def list_lineage_stub(): return []

@router.get("/policy-proposals")
async def list_policies_stub(): return []

@router.get("/self-tuning")
async def list_tuning_stub(): return []

@router.get("/projects")
async def list_projects_stub(): return []

@router.get("/analytics/costs/summary")
async def legacy_cost_summary_stub():
    return {
        "total_cost_usd": 0.0,
        "budget_limit_usd": 1000.0,
        "usage_pct": 0.0,
        "top_projects": [],
    }
