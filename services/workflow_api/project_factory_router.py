from __future__ import annotations

import os
import json
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from services.auth.jwt_auth import require_permission
from services.project_factory.models import (
    ApproveScopeRequest,
    RequestRevisionRequest,
    RejectRequest,
    ImplementationStartRequest,
    ApproveDeliveryRequest,
    RevisionRequest,
    RejectCandidateRequest,
    DraftPrCreateRequest,
    PrReviewRunRequest,
    PrReviewDecisionRequest,
    FinalApproveRequest,
    FinalRejectRequest,
    FinalRevisionRequest,
)
from services.project_factory.artifacts import (
    load_project_factory_artifacts,
    _resolve_project_dir
)
from services.project_factory.gate_service import (
    approve_project_scope,
    request_project_revision,
    reject_project_intake
)
from services.project_factory.gate_logs import get_gate_decisions
from services.project_factory.implementation_runner import (
    start_sandbox_implementation,
    get_implementation_run,
    cancel_sandbox_implementation
)
from services.project_factory.task_planner import load_task_breakdown
from services.project_factory.verification_runner import load_verification_report
from services.project_factory.candidate_packager import load_candidate_manifest
from services.project_factory.implementation_logs import get_implementation_events

from services.project_factory.candidate_review import run_candidate_review, load_candidate_review
from services.project_factory.human_gate_service import (
    approve_candidate_delivery,
    request_candidate_revision,
    reject_candidate_delivery
)
from services.project_factory.delivery_packager import load_delivery_manifest
from services.project_factory.delivery_logs import get_delivery_decisions
from services.project_factory.artifacts import load_draft_pr_creation
from services.project_factory.pr_creation_service import execute_pr_creation, abort_pr_creation
from services.project_factory.pr_creation_logs import get_pr_creation_logs
from services.project_factory.git_workspace import GitSafetyViolation
from services.project_factory.pr_review_gate import run_pr_review_gate
from services.project_factory.pr_review_decision import apply_pr_review_decision
from services.project_factory.pr_review_logs import get_pr_review_decisions
from services.project_factory.artifacts import load_pr_review_report
from services.project_factory.final_decision_service import final_approve, final_reject, final_request_revision
from services.project_factory.artifacts import load_final_operator_decision, load_release_manifest
from services.project_factory.final_decision_logs import get_final_decision_logs

router = APIRouter(tags=["Project Factory Gate Core"])

@router.get("/{project_id}")
async def get_project_factory_detail(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """
    Retrieves the complete project brief and requirement gate status for a given Project Factory intake.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        brief, gate = load_project_factory_artifacts(project_id, workspace_root)
        return {
            "status": "success",
            "project_brief": brief.model_dump(),
            "requirement_gate": gate.model_dump()
        }
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load project details: {e}")

@router.post("/{project_id}/requirement-gate/approve-scope")
async def approve_scope_endpoint(
    project_id: str,
    body: ApproveScopeRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Operator approves project scope, triggering sandbox scaffolding.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = approve_project_scope(project_id, body, workspace_root)
        return result
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approve scope failed: {e}")

@router.post("/{project_id}/requirement-gate/request-revision")
async def request_revision_endpoint(
    project_id: str,
    body: RequestRevisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Operator requests scope revision.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = request_project_revision(project_id, body, workspace_root)
        return result
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Request revision failed: {e}")

@router.post("/{project_id}/requirement-gate/reject")
async def reject_endpoint(
    project_id: str,
    body: RejectRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Operator rejects project intake.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = reject_project_intake(project_id, body, workspace_root)
        return result
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reject failed: {e}")

@router.get("/{project_id}/artifacts")
async def get_project_artifacts(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """
    Retrieves all artifacts generated for the project, including brief, gate status, sandbox manifest, and history of decisions.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        brief, gate = load_project_factory_artifacts(project_id, workspace_root)
        project_dir = _resolve_project_dir(project_id, workspace_root)
        
        manifest_data = None
        manifest_path = project_dir / "sandbox_manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)

        decisions = get_gate_decisions(project_id, workspace_root)

        return {
            "status": "success",
            "project_brief": brief.model_dump(),
            "requirement_gate": gate.model_dump(),
            "sandbox_manifest": manifest_data,
            "decisions": decisions
        }
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load artifacts: {e}")

@router.post("/{project_id}/implementation/start")
async def start_implementation_endpoint(
    project_id: str,
    body: ImplementationStartRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Starts the sandbox implementation runner.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        run_data = start_sandbox_implementation(
            project_id=project_id,
            operator_id=body.operator_id,
            rationale=body.rationale,
            runner_mode=body.runner_mode,
            workspace_root=workspace_root
        )
        return {
            "status": "success",
            "implementation_run": run_data
        }
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start implementation: {e}")

@router.get("/{project_id}/implementation/status")
async def get_implementation_status_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """
    Retrieves the current status snapshot of the implementation runner.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        run_data = get_implementation_run(project_id, workspace_root)
        if not run_data:
            raise HTTPException(status_code=404, detail=f"No implementation run found for project {project_id}")
        
        breakdown = load_task_breakdown(project_id, workspace_root)
        events = get_implementation_events(project_id, workspace_root)
        
        return {
            "status": "success",
            "implementation_run": run_data,
            "task_breakdown": [t.model_dump() for t in breakdown],
            "events": events
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load status: {e}")

@router.get("/{project_id}/implementation/report")
async def get_implementation_report_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """
    Retrieves implementation and verification reports.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        run_data = get_implementation_run(project_id, workspace_root)
        verification = load_verification_report(project_id, workspace_root)
        
        return {
            "status": "success",
            "implementation_run": run_data,
            "verification_report": verification
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load report: {e}")

@router.post("/{project_id}/implementation/cancel")
async def cancel_implementation_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Cancels an active sandbox implementation runner.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        run_data = cancel_sandbox_implementation(project_id, workspace_root)
        return {
            "status": "success",
            "implementation_run": run_data
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel implementation: {e}")

@router.get("/{project_id}/candidate-package")
async def get_candidate_package_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """
    Retrieves candidate package details and checksum manifest.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        manifest = load_candidate_manifest(project_id, workspace_root)
        if not manifest:
            raise HTTPException(status_code=404, detail=f"No candidate package manifest found for project {project_id}")
        return {
            "status": "success",
            "candidate_manifest": manifest
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load candidate package details: {e}")

@router.post("/{project_id}/candidate/review")
async def run_candidate_review_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Triggers the candidate review pipeline, scoring and risk assessment.
    Transitions state to CANDIDATE_REVIEWED.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        review = run_candidate_review(project_id, workspace_root)
        return {
            "status": "success",
            "candidate_review": review.model_dump()
        }
    except FileNotFoundError as fe:
        raise HTTPException(status_code=404, detail=str(fe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run candidate review: {e}")

@router.get("/{project_id}/candidate/review")
async def get_candidate_review_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """
    Retrieves the candidate review details, scorecard and risk assessment.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_dir = _resolve_project_dir(project_id, workspace_root)
    try:
        review = load_candidate_review(project_id, workspace_root)
        if not review:
            raise HTTPException(status_code=404, detail=f"No candidate review found for project {project_id}")

        scorecard = None
        scorecard_path = project_dir / "quality_scorecard.json"
        if scorecard_path.exists():
            with open(scorecard_path, "r", encoding="utf-8") as f:
                scorecard = json.load(f)

        risk_assessment = None
        risk_path = project_dir / "risk_assessment.json"
        if risk_path.exists():
            with open(risk_path, "r", encoding="utf-8") as f:
                risk_assessment = json.load(f)

        return {
            "status": "success",
            "candidate_review": review,
            "quality_scorecard": scorecard,
            "risk_assessment": risk_assessment
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve candidate review: {e}")

@router.post("/{project_id}/human-gate/approve-delivery")
async def approve_delivery_endpoint(
    project_id: str,
    body: ApproveDeliveryRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Approves candidate and creates delivery package.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = approve_candidate_delivery(project_id, body, workspace_root)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve delivery: {e}")

@router.post("/{project_id}/human-gate/request-revision")
async def request_candidate_revision_endpoint(
    project_id: str,
    body: RevisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Operator requests revision on the candidate.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = request_candidate_revision(project_id, body, workspace_root)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to request revision: {e}")

@router.post("/{project_id}/human-gate/reject")
async def reject_candidate_endpoint(
    project_id: str,
    body: RejectCandidateRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Operator rejects candidate.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = reject_candidate_delivery(project_id, body, workspace_root)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject candidate: {e}")

@router.get("/{project_id}/delivery-package")
async def get_delivery_package_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """
    Retrieves final delivery package manifest and release notes content.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_dir = _resolve_project_dir(project_id, workspace_root)
    try:
        manifest = load_delivery_manifest(project_id, workspace_root)
        if not manifest:
            raise HTTPException(status_code=404, detail=f"No delivery package manifest found for project {project_id}")

        release_notes = ""
        rn_path = project_dir / "delivery_package" / "release_notes.md"
        if rn_path.exists():
            release_notes = rn_path.read_text(encoding="utf-8")

        return {
            "status": "success",
            "delivery_manifest": manifest,
            "release_notes": release_notes
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve delivery package: {e}")

@router.get("/{project_id}/delivery/logs")
async def get_delivery_logs_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    """
    Retrieves the append-only logs of operator actions on candidate/delivery gates.
    """
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        logs = get_delivery_decisions(project_id, workspace_root)
        return {
            "status": "success",
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve delivery logs: {e}")

@router.post("/{project_id}/draft-pr/create")
async def create_draft_pr_endpoint(
    project_id: str,
    body: DraftPrCreateRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = execute_pr_creation(project_id, body, workspace_root)
        return {"status": "success", "draft_pr_creation": result.model_dump()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except GitSafetyViolation as gse:
        raise HTTPException(status_code=403, detail=str(gse))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Draft PR creation failed: {e}")

@router.get("/{project_id}/draft-pr/status")
async def get_draft_pr_status_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        data = load_draft_pr_creation(project_id, workspace_root)
        if not data:
            raise HTTPException(status_code=404, detail="No Draft PR creation data found.")
        return {"status": "success", "draft_pr_creation": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PR status: {e}")

@router.get("/{project_id}/draft-pr/logs")
async def get_draft_pr_logs_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        logs = get_pr_creation_logs(project_id, workspace_root)
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load logs: {e}")

@router.post("/{project_id}/draft-pr/abort")
async def abort_draft_pr_endpoint(
    project_id: str,
    body: RejectCandidateRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = abort_pr_creation(project_id, body.operator_id, body.rationale, workspace_root)
        return {"status": "success", "draft_pr_creation": result.model_dump()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Abort failed: {e}")

@router.post("/{project_id}/pr-review/run")
async def run_pr_review_endpoint(
    project_id: str,
    body: PrReviewRunRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = run_pr_review_gate(project_id, body, workspace_root)
        return {"status": "success", "pr_review_report": result.model_dump()}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR review failed: {e}")

@router.get("/{project_id}/pr-review")
async def get_pr_review_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        data = load_pr_review_report(project_id, workspace_root)
        if not data:
            raise HTTPException(status_code=404, detail="No PR review report found.")
        return {"status": "success", "pr_review_report": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PR review: {e}")

@router.post("/{project_id}/pr-review/decision")
async def pr_review_decision_endpoint(
    project_id: str,
    body: PrReviewDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = apply_pr_review_decision(project_id, body, workspace_root)
        return {"status": "success", "decision_result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision failed: {e}")

@router.get("/{project_id}/pr-review/logs")
async def get_pr_review_logs_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        logs = get_pr_review_decisions(project_id, workspace_root)
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PR review logs: {e}")

@router.post("/{project_id}/final-decision/approve")
async def final_approve_endpoint(
    project_id: str,
    body: FinalApproveRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = final_approve(project_id, body, workspace_root)
        return {"status": "success", **result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Final approve failed: {e}")

@router.post("/{project_id}/final-decision/reject")
async def final_reject_endpoint(
    project_id: str,
    body: FinalRejectRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = final_reject(project_id, body, workspace_root)
        return {"status": "success", **result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Final reject failed: {e}")

@router.post("/{project_id}/final-decision/request-revision")
async def final_revision_endpoint(
    project_id: str,
    body: FinalRevisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = final_request_revision(project_id, body, workspace_root)
        return {"status": "success", **result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Final revision failed: {e}")

@router.get("/{project_id}/final-decision")
async def get_final_decision_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        data = load_final_operator_decision(project_id, workspace_root)
        if not data:
            raise HTTPException(status_code=404, detail="No final decision found.")
        return {"status": "success", "final_decision": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load final decision: {e}")

@router.get("/{project_id}/release-archive")
async def get_release_archive_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        manifest = load_release_manifest(project_id, workspace_root)
        if not manifest:
            raise HTTPException(status_code=404, detail="No release archive found.")
        # Load closure report content
        from services.project_factory.artifacts import _resolve_project_dir
        project_dir = _resolve_project_dir(project_id, workspace_root)
        closure_path = project_dir / "release_archive" / "closure_report.md"
        closure_report = ""
        if closure_path.exists():
            closure_report = closure_path.read_text(encoding="utf-8")
        return {"status": "success", "release_manifest": manifest, "closure_report": closure_report}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load release archive: {e}")

@router.get("/{project_id}/release-archive/logs")
async def get_release_archive_logs_endpoint(
    project_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        logs = get_final_decision_logs(project_id, workspace_root)
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load final decision logs: {e}")

# --- Phase 13: Archive Index + Portfolio View Endpoints ---

from services.project_factory.models import RebuildArchiveRequest
from services.project_factory.portfolio_service import rebuild_portfolio
from services.project_factory.artifacts import load_archive_index, load_portfolio_metrics
from services.project_factory.archive_search import search_archive
from services.project_factory.artifacts import _resolve_project_factory_root

@router.post("/archive-index/rebuild")
async def rebuild_archive_index_endpoint(
    body: RebuildArchiveRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = rebuild_portfolio(body, workspace_root)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild archive index: {e}")

@router.get("/archive-index")
async def get_archive_index_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        data = load_archive_index(workspace_root)
        if not data:
            return {"status": "success", "archive_index": {"total_projects": 0, "projects": []}}
        return {"status": "success", "archive_index": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load archive index: {e}")

@router.get("/portfolio/metrics")
async def get_portfolio_metrics_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        data = load_portfolio_metrics(workspace_root)
        if not data:
            return {"status": "success", "metrics": {}}
        return {"status": "success", "metrics": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load portfolio metrics: {e}")

@router.get("/portfolio/search")
async def search_portfolio_endpoint(
    q: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    has_release_archive: Optional[bool] = None,
    final_decision: Optional[str] = None,
    sort: str = "updated_at_desc",
    limit: int = 20,
    offset: int = 0,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        results = search_archive(
            query=q,
            status=status,
            risk_level=risk_level,
            has_release_archive=has_release_archive,
            final_decision=final_decision,
            sort=sort,
            limit=limit,
            offset=offset,
            workspace_root=workspace_root
        )
        return {"status": "success", "search_results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

@router.get("/archive-index/logs")
async def get_archive_index_logs_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        root = _resolve_project_factory_root(workspace_root)
        log_path = root / "archive_index_logs.jsonl"
        logs = []
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load archive index logs: {e}")

# --- Phase 14: Portfolio Intelligence + Learning Memory Feedback Endpoints ---

from services.project_factory.models import RunIntelligenceRequest, CEOSuggestionsPublishRequest
from services.project_factory.portfolio_intelligence import run_portfolio_intelligence, publish_ceo_suggestions
from services.project_factory.artifacts import load_portfolio_intelligence

@router.post("/portfolio/intelligence/run")
async def run_portfolio_intelligence_endpoint(
    body: RunIntelligenceRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = run_portfolio_intelligence(body, workspace_root)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run portfolio intelligence: {e}")

@router.get("/portfolio/intelligence")
async def get_portfolio_intelligence_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        data = load_portfolio_intelligence(workspace_root)
        if not data:
            raise HTTPException(status_code=404, detail="Portfolio intelligence not found.")
        return {"status": "success", "intelligence": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load portfolio intelligence: {e}")

@router.get("/portfolio/intelligence/logs")
async def get_portfolio_intelligence_logs_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        root = _resolve_project_factory_root(workspace_root)
        log_path = root / "portfolio_intelligence_logs.jsonl"
        logs = []
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load portfolio intelligence logs: {e}")

@router.post("/portfolio/intelligence/publish-ceo-suggestions")
async def publish_ceo_suggestions_endpoint(
    body: CEOSuggestionsPublishRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = publish_ceo_suggestions(body, workspace_root)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish CEO suggestions: {e}")

# --- Phase 15: Portfolio Policy Autopilot Endpoints ---

from services.project_factory.models import RunPolicyAutopilotRequest, PolicyProposalDecisionRequest
from services.project_factory.policy_autopilot import (
    run_policy_autopilot,
    get_policy_autopilot_data,
    approve_for_policy_board,
    defer_policy_proposal,
    reject_policy_proposal
)

@router.post("/portfolio/policy-autopilot/run")
async def run_policy_autopilot_endpoint(
    body: RunPolicyAutopilotRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return run_policy_autopilot(body, workspace_root)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run policy autopilot: {e}")

@router.get("/portfolio/policy-autopilot")
async def get_policy_autopilot_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return get_policy_autopilot_data(workspace_root)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policy autopilot data: {e}")

@router.get("/portfolio/policy-autopilot/logs")
async def get_policy_autopilot_logs_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from services.project_factory.artifacts import _resolve_policy_autopilot_dir
        d = _resolve_policy_autopilot_dir(workspace_root)
        log_path = d / "policy_autopilot_logs.jsonl"
        logs = []
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policy autopilot logs: {e}")

@router.post("/portfolio/policy-autopilot/{proposal_id}/approve-for-policy-board")
async def approve_for_policy_board_endpoint(
    proposal_id: str,
    body: PolicyProposalDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return approve_for_policy_board(proposal_id, body, workspace_root)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve proposal: {e}")

@router.post("/portfolio/policy-autopilot/{proposal_id}/defer")
async def defer_policy_proposal_endpoint(
    proposal_id: str,
    body: PolicyProposalDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return defer_policy_proposal(proposal_id, body, workspace_root)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to defer proposal: {e}")

@router.post("/portfolio/policy-autopilot/{proposal_id}/reject")
async def reject_policy_proposal_endpoint(
    proposal_id: str,
    body: PolicyProposalDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return reject_policy_proposal(proposal_id, body, workspace_root)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject proposal: {e}")

# --- Phase 16: Policy Board Decision & Apply Preview Endpoints ---

from services.project_factory.models import PolicyBoardDecisionRequest
from services.project_factory.policy_board_service import approve_for_preview, request_revision, reject_proposal
from services.project_factory.policy_apply_preview import generate_apply_preview
from services.project_factory.artifacts import load_policy_apply_preview, load_policy_board_package
from services.project_factory.policy_board_package import generate_policy_board_package

@router.post("/portfolio/policy-board/{proposal_id}/approve-for-preview")
async def board_approve_for_preview_endpoint(
    proposal_id: str,
    body: PolicyBoardDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return approve_for_preview(proposal_id, body, workspace_root)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve for preview: {e}")

@router.post("/portfolio/policy-board/{proposal_id}/request-revision")
async def board_request_revision_endpoint(
    proposal_id: str,
    body: PolicyBoardDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return request_revision(proposal_id, body, workspace_root)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to request revision: {e}")

@router.post("/portfolio/policy-board/{proposal_id}/reject")
async def board_reject_proposal_endpoint(
    proposal_id: str,
    body: PolicyBoardDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return reject_proposal(proposal_id, body, workspace_root)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject proposal: {e}")

@router.post("/portfolio/policy-board/{proposal_id}/apply-preview")
async def board_run_apply_preview_endpoint(
    proposal_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        return generate_apply_preview(proposal_id, workspace_root)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate apply preview: {e}")

@router.get("/portfolio/policy-board/{proposal_id}/apply-preview")
async def board_get_apply_preview_endpoint(
    proposal_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        # Simplification: just return the latest preview
        preview = load_policy_apply_preview(workspace_root)
        if not preview:
            return {"status": "success", "preview": None}
        if preview.get("proposal_id") != proposal_id:
            return {"status": "success", "preview": None}
        return {"status": "success", "preview": preview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load apply preview: {e}")

@router.get("/portfolio/policy-board/logs")
async def board_get_logs_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from services.project_factory.artifacts import _resolve_policy_autopilot_dir
        d = _resolve_policy_autopilot_dir(workspace_root)
        log_path = d / "policy_board_decisions.jsonl"
        logs = []
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load board logs: {e}")

@router.get("/portfolio/policy-board/package")
async def board_get_package_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        pkg = generate_policy_board_package(workspace_root)
        return {"status": "success", "package": pkg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate package: {e}")

# --- Phase 17: Policy Draft PR Plan & Governance Evidence Endpoints ---
from services.project_factory.models import PolicyDraftPRPlanRequest
from services.project_factory.policy_draft_pr_planner import prepare_draft_pr_plan
from services.project_factory.policy_governance_packager import generate_governance_evidence_pack
from services.project_factory.artifacts import load_policy_draft_pr_plan, load_policy_governance_manifest
from services.project_factory.policy_pr_plan_logs import load_policy_pr_plan_logs

@router.post("/portfolio/policy-pr-plan/{proposal_id}/prepare")
async def pr_plan_prepare_endpoint(
    proposal_id: str,
    body: PolicyDraftPRPlanRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        plan = prepare_draft_pr_plan(proposal_id, body)
        # Generate the evidence pack right after successful preparation
        pack = generate_governance_evidence_pack(proposal_id, workspace_root)
        return {"status": "success", "plan": plan, "evidence_manifest": pack}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prepare plan failed: {e}")

@router.get("/portfolio/policy-pr-plan/{proposal_id}")
async def pr_plan_get_endpoint(
    proposal_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        plan = load_policy_draft_pr_plan(workspace_root)
        if not plan or plan.get("proposal_id") != proposal_id:
            return {"status": "success", "plan": None}
        return {"status": "success", "plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load draft PR plan: {e}")

@router.get("/portfolio/policy-pr-plan/{proposal_id}/evidence-pack")
async def evidence_pack_get_endpoint(
    proposal_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        manifest = load_policy_governance_manifest(workspace_root)
        if not manifest or manifest.get("proposal_id") != proposal_id:
            return {"status": "success", "manifest": None}
        return {"status": "success", "manifest": manifest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load evidence manifest: {e}")

@router.get("/portfolio/policy-pr-plan/logs")
async def pr_plan_logs_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        logs = load_policy_pr_plan_logs(workspace_root)
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PR plan logs: {e}")

# --- Phase 18: Operator-Approved Policy Draft PR Creation Endpoints ---
from services.project_factory.models import PolicyPRCreationRequest
from services.project_factory.policy_pr_creation_service import execute_policy_pr_creation
from services.project_factory.artifacts import load_policy_pr_creation, load_policy_pr_status
from services.project_factory.policy_pr_creation_logs import load_policy_pr_creation_logs

@router.post("/portfolio/policy-pr-plan/{proposal_id}/create-pr")
async def create_policy_pr_endpoint(
    proposal_id: str,
    body: PolicyPRCreationRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = execute_policy_pr_creation(proposal_id, body, workspace_root)
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Create PR failed: {e}")

@router.get("/portfolio/policy-pr-plan/{proposal_id}/creation-status")
async def get_policy_pr_status_endpoint(
    proposal_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        status_data = load_policy_pr_status(workspace_root)
        creation_data = load_policy_pr_creation(workspace_root)
        if not status_data or status_data.get("proposal_id") != proposal_id:
            return {"status": "success", "creation_status": None, "creation_data": None}
        return {"status": "success", "creation_status": status_data, "creation_data": creation_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PR status: {e}")

@router.get("/portfolio/policy-pr-plan/creation-logs")
async def get_policy_pr_creation_logs_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        logs = load_policy_pr_creation_logs(workspace_root)
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PR creation logs: {e}")

# --- Phase 19: Policy PR Review Gate + Verifier Mesh Endpoints ---
from services.project_factory.models import PolicyPRReviewRunRequest, PolicyPRReviewDecisionRequest
from services.project_factory.policy_pr_review_gate import run_policy_pr_review_gate
from services.project_factory.policy_pr_review_decision import execute_policy_pr_review_decision
from services.project_factory.artifacts import load_policy_pr_review_report
from services.project_factory.policy_pr_review_logs import load_policy_pr_review_logs

@router.post("/portfolio/policy-pr-review/{proposal_id}/run")
async def run_policy_pr_review_endpoint(
    proposal_id: str,
    body: PolicyPRReviewRunRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = run_policy_pr_review_gate(proposal_id, body, workspace_root)
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run PR review: {e}")

@router.get("/portfolio/policy-pr-review/{proposal_id}")
async def get_policy_pr_review_endpoint(
    proposal_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        report = load_policy_pr_review_report(workspace_root)
        if not report or report.get("proposal_id") != proposal_id:
            return {"status": "success", "report": None}
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PR review: {e}")

@router.post("/portfolio/policy-pr-review/{proposal_id}/decision")
async def execute_policy_pr_review_decision_endpoint(
    proposal_id: str,
    body: PolicyPRReviewDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = execute_policy_pr_review_decision(proposal_id, body, workspace_root)
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute PR review decision: {e}")

@router.get("/portfolio/policy-pr-review/logs")
async def get_policy_pr_review_logs_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        logs = load_policy_pr_review_logs(workspace_root)
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PR review logs: {e}")

# --- Phase 20: Policy Final Decision + Release Archive Endpoints ---
from services.project_factory.models import PolicyFinalDecisionRequest, PolicyFinalRevisionRequest
from services.project_factory.policy_final_decision_service import (
    execute_final_approve,
    execute_final_reject,
    execute_final_revision_request
)
from services.project_factory.artifacts import load_policy_release_manifest
from services.project_factory.policy_final_decision_logs import load_policy_final_decision_logs

@router.post("/portfolio/policy-final/{proposal_id}/approve")
async def execute_final_approve_endpoint(
    proposal_id: str,
    body: PolicyFinalDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = execute_final_approve(proposal_id, body, workspace_root)
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute final approve: {e}")

@router.post("/portfolio/policy-final/{proposal_id}/reject")
async def execute_final_reject_endpoint(
    proposal_id: str,
    body: PolicyFinalDecisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = execute_final_reject(proposal_id, body, workspace_root)
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute final reject: {e}")

@router.post("/portfolio/policy-final/{proposal_id}/request-revision")
async def execute_final_revision_request_endpoint(
    proposal_id: str,
    body: PolicyFinalRevisionRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        result = execute_final_revision_request(proposal_id, body, workspace_root)
        return {"status": "success", "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute final revision request: {e}")

@router.get("/portfolio/policy-final/{proposal_id}/release-archive")
async def get_policy_final_release_archive_endpoint(
    proposal_id: str,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        manifest = load_policy_release_manifest(workspace_root)
        if not manifest or manifest.get("proposal_id") != proposal_id:
            return {"status": "success", "manifest": None}
        return {"status": "success", "manifest": manifest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load release archive: {e}")

@router.get("/portfolio/policy-final/logs")
async def get_policy_final_decision_logs_endpoint(
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        logs = load_policy_final_decision_logs(workspace_root)
        return {"status": "success", "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load final decision logs: {e}")
