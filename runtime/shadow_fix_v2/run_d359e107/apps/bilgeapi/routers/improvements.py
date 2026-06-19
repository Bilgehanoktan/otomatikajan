from datetime import datetime, timezone
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Response

from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.repositories.interface import ResearchRepository, ImprovementRepository
from apps.bilgeapi.services.research import WebResearchAdapter
from apps.bilgeapi.services.improvement import ImprovementProposalEngine, ReleaseGateSimulator
from apps.bilgeapi.schemas.improvements import (
    ResearchCreate, ResearchResponse, EvidenceResponse, ProposalResponse, DraftPrResponse
)
from apps.bilgeapi.schemas.pr_draft import PrDraftResponse
from apps.bilgeapi.schemas.pr_verification import PrVerificationResponse, PrReviewReportResponse
from apps.bilgeapi.schemas.pr_revision import (
    ReviewerFeedbackRequest, ReviewerFeedbackResponse, PatchRevisionRequest, PatchRevisionResponse
)
from apps.bilgeapi.schemas.ai_patch_suggestion import (
    AIPatchSuggestionDecisionRequest,
    AIPatchSuggestionDecisionResponse,
    AIPatchSuggestionRequest,
    AIPatchSuggestionResponse,
)
from apps.bilgeapi.routers.deps import (
    get_research_repository,
    get_improvement_repository,
    get_web_research_adapter,
    get_improvement_proposal_engine,
    get_release_gate_simulator,
    get_pr_draft_service,
    get_pr_draft_repository,
    get_pr_verification_service,
    get_pr_verification_repository,
    get_reviewer_feedback_service,
    get_patch_revision_engine,
    get_pr_review_feedback_repository,
    get_patch_revision_repository,
    get_ai_patch_suggestion_repository,
    get_ai_patch_suggestion_service,
)

router = APIRouter(prefix="/v1/improvements", tags=["Improvements"])


@router.post("/research", response_model=ResearchResponse, status_code=status.HTTP_201_CREATED)
async def create_research(
    body: ResearchCreate,
    identity: dict = Depends(require_permission("bilgeapi.incident.write")),
    repo: ResearchRepository = Depends(get_research_repository),
    adapter: WebResearchAdapter = Depends(get_web_research_adapter)
):
    """
    Start research on an incident query. Enforces tenant-based daily quota limit of 5 requests.
    """
    tenant_id = identity.get("tenant_id") or "default_tenant"

    # Check tenant daily quota limit
    daily_count = await repo.get_tenant_daily_research_count(tenant_id, datetime.now(timezone.utc))
    if daily_count >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily research quota exceeded for tenant"
        )

    request_data = {
        "incident_id": body.incident_id,
        "query": body.query,
        "status": "PENDING",
        "tenant_id": tenant_id
    }
    req = await repo.create_request(request_data)

    # Execute research (grade sources, save evidences, update status to COMPLETED)
    await adapter.run_research(req["id"])

    # Re-fetch request to get updated status
    updated = await repo.get_request(req["id"])
    if not updated:
        raise HTTPException(status_code=404, detail="Research request not found after execution")
    return updated


@router.get("/research/{research_id}", response_model=ResearchResponse)
async def get_research(
    research_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.read")),
    repo: ResearchRepository = Depends(get_research_repository)
):
    """
    Retrieve a research request.
    """
    req = await repo.get_request(research_id)
    if not req:
        raise HTTPException(status_code=404, detail="Research request not found")
    return req


@router.get("/research/{research_id}/evidences", response_model=List[EvidenceResponse])
async def list_evidences(
    research_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.read")),
    repo: ResearchRepository = Depends(get_research_repository)
):
    """
    List graded research evidences for a request.
    """
    evidences = await repo.list_evidences(research_id)
    return evidences


@router.post("/{research_id}/proposal", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(
    research_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.write")),
    engine: ImprovementProposalEngine = Depends(get_improvement_proposal_engine)
):
    """
    Generate an improvement proposal and patch draft based on a research request.
    """
    try:
        proposal = await engine.generate_proposal(research_id)
        return proposal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/proposals/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.read")),
    repo: ImprovementRepository = Depends(get_improvement_repository)
):
    """
    Retrieve an improvement proposal.
    """
    proposal = await repo.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.get("/proposals", response_model=List[ProposalResponse])
async def list_proposals(
    _identity: dict = Depends(require_permission("bilgeapi.incident.read")),
    repo: ImprovementRepository = Depends(get_improvement_repository)
):
    """
    List all improvement proposals.
    """
    proposals = await repo.list_proposals()
    return proposals


@router.get("/proposals/{proposal_id}/audit-report")
async def get_audit_report(
    proposal_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.read")),
    proposal_repo: ImprovementRepository = Depends(get_improvement_repository),
    research_repo: ResearchRepository = Depends(get_research_repository),
    simulator: ReleaseGateSimulator = Depends(get_release_gate_simulator)
):
    """
    Retrieve the generated self-improvement markdown audit report.
    """
    proposal = await proposal_repo.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    evidences = await research_repo.list_evidences(proposal["research_id"])
    report = simulator.generate_audit_report(proposal, evidences)
    return Response(content=report, media_type="text/markdown")


@router.post("/{proposal_id}/draft-pr", response_model=DraftPrResponse)
async def create_draft_pr(
    proposal_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.write")),
    repo: ImprovementRepository = Depends(get_improvement_repository)
):
    """
    Generate draft PR metadata and patch details. Prohibits auto-applying or merging.
    """
    proposal = await repo.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    risk_analysis = proposal.get("risk_analysis") or {}
    affected_files = risk_analysis.get("affected_files", ["apps/bilgeapi/main.py"])
    confidence_score = risk_analysis.get("confidence_score", 0.0)
    confidence_level = risk_analysis.get("confidence_level", "UNKNOWN")

    description = (
        f"### 1. Problem Özeti\n"
        f"Autonomous self-improvement proposal based on request query: '{proposal['title']}'.\n\n"
        f"### 2. Kullanılan Kaynaklar & Trust Scores\n"
        f"Confidence Score: {confidence_score:.2f} ({confidence_level})\n"
        f"Evidence summary details:\n"
        f"{proposal['rationale']}\n\n"
        f"### 3. Önerilen Değişiklik\n"
        f"Autonomous code patch designed to resolve potential issues:\n"
        f"```diff\n{proposal['patch_code']}```\n\n"
        f"### 4. Etkilenen Dosyalar\n"
        + "\n".join(f"- `{f}`" for f in affected_files) + "\n\n"
        f"### 5. Risk Analizi\n"
        f"- Risk Level: {risk_analysis.get('risk_level', 'LOW')}\n"
        f"- Potential Side Effects: {risk_analysis.get('potential_side_effects', 'None expected.')}\n"
        f"- Mitigation Plan: {risk_analysis.get('mitigation_plan', 'None')}\n\n"
        f"### 6. Test Planı\n"
        f"- Execute simulated release gate checks (/run-gate).\n"
        f"- Run functional integration tests.\n\n"
        f"### 7. Rollback Planı\n"
        f"Discard changes by resetting the files via git or reverting the applied commit."
    )

    return DraftPrResponse(
        patch_code=proposal["patch_code"],
        title=f"Draft PR: {proposal['title']}",
        description=description,
        risk_level=risk_analysis.get("risk_level", "LOW"),
        affected_files=affected_files,
        potential_side_effects=risk_analysis.get("potential_side_effects", "None expected."),
        mitigation_plan=risk_analysis.get("mitigation_plan", "Run simulated release gate checks.")
    )


@router.post("/{proposal_id}/run-gate")
async def run_gate(
    proposal_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.write")),
    simulator: ReleaseGateSimulator = Depends(get_release_gate_simulator)
):
    """
    Run simulated gate impact checks on the proposal.
    """
    try:
        report = await simulator.run_simulation(proposal_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{proposal_id}/approve", response_model=ProposalResponse)
async def approve_proposal(
    proposal_id: str,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    repo: ImprovementRepository = Depends(get_improvement_repository)
):
    """
    Approve an improvement proposal, flagging it as ready_for_human_apply.
    Prohibits approval if confidence level is LOW or if status is REJECTED.
    """
    proposal = await repo.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    risk_analysis = proposal.get("risk_analysis") or {}
    confidence_level = risk_analysis.get("confidence_level")

    if confidence_level == "LOW" or proposal.get("approval_status") == "REJECTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Low-confidence proposals cannot be approved."
        )

    actor_id = identity.get("id", "admin")
    approved = await repo.approve_proposal(
        proposal_id=proposal_id,
        approved_by=actor_id,
        approved_at=datetime.now(timezone.utc)
    )
    return approved


@router.post("/proposals/{proposal_id}/draft-pr/create", response_model=PrDraftResponse)
async def create_draft_pr_endpoint(
    proposal_id: str,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_pr_draft_service)
):
    """
    Trigger Safe Draft PR creation for an approved, gate-passed proposal.
    Admin permission (bilgeapi.admin) is required.
    """
    actor_id = identity.get("id", "admin")
    try:
        pr_draft = await service.create_draft_pr(proposal_id=proposal_id, actor_id=actor_id)
        return pr_draft
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/proposals/{proposal_id}/draft-prs", response_model=List[PrDraftResponse])
async def list_draft_prs_endpoint(
    proposal_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.incident.write")),
    repo: Any = Depends(get_pr_draft_repository)
):
    """
    Get the list of draft PRs created for a specific proposal.
    """
    try:
        return await repo.list_pr_drafts_by_proposal(proposal_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/pr-drafts/{pr_draft_id}/verify", response_model=PrVerificationResponse, status_code=status.HTTP_201_CREATED)
async def verify_pr_draft_endpoint(
    pr_draft_id: str,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_pr_verification_service)
):
    """
    Trigger Sandbox verification and PR Review Gate scoring for a Draft PR. Admin-only.
    """
    actor_id = identity.get("id", "admin")
    try:
        verification = await service.verify_pr_draft(pr_draft_id=pr_draft_id, actor_id=actor_id)
        return verification
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pr-drafts/{pr_draft_id}/verification", response_model=PrVerificationResponse)
async def get_pr_verification_endpoint(
    pr_draft_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: Any = Depends(get_pr_verification_repository)
):
    """
    Get the latest sandbox verification record for a Draft PR. Operator or Admin.
    """
    try:
        verification = await repo.get_verification_by_pr_draft(pr_draft_id)
        if not verification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No verification record found for this PR draft")
        return verification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pr-drafts/{pr_draft_id}/review-report", response_model=PrReviewReportResponse)
async def get_pr_review_report_endpoint(
    pr_draft_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: Any = Depends(get_pr_verification_repository)
):
    """
    Get the markdown PR review report for a Draft PR. Operator or Admin.
    """
    try:
        verification = await repo.get_verification_by_pr_draft(pr_draft_id)
        if not verification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No verification report found for this PR draft")
        
        return PrReviewReportResponse(
            pr_draft_id=verification["pr_draft_id"],
            proposal_id=verification["proposal_id"],
            review_score=verification["review_score"],
            review_decision=verification["review_decision"],
            risk_level=verification["risk_level"],
            report_markdown=verification["verification_report"] or "",
            created_at=verification["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/pr-drafts/{pr_draft_id}/feedback", response_model=ReviewerFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback_endpoint(
    pr_draft_id: str,
    body: ReviewerFeedbackRequest,
    identity: dict = Depends(require_permission("bilgeapi.operator")),
    service: Any = Depends(get_reviewer_feedback_service)
):
    """
    Add reviewer feedback to a Draft PR. Operator or Admin.
    """
    actor_id = identity.get("id", "operator")
    try:
        fb = await service.add_feedback(
            pr_draft_id=pr_draft_id,
            comment=body.comment,
            reviewer_id=body.reviewer_id,
            actor_id=actor_id
        )
        return fb
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pr-drafts/{pr_draft_id}/feedback", response_model=List[ReviewerFeedbackResponse])
async def list_feedback_endpoint(
    pr_draft_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: Any = Depends(get_pr_review_feedback_repository)
):
    """
    List all reviewer feedback for a Draft PR. Operator or Admin.
    """
    try:
        feedbacks = await repo.list_feedback_by_pr_draft(pr_draft_id)
        return feedbacks
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/pr-drafts/{pr_draft_id}/revisions", response_model=PatchRevisionResponse, status_code=status.HTTP_201_CREATED)
async def create_revision_endpoint(
    pr_draft_id: str,
    body: PatchRevisionRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_patch_revision_engine)
):
    """
    Create a new patch revision for a Draft PR. Admin-only.
    """
    actor_id = identity.get("id", "admin")
    try:
        rev = await service.create_revision(
            pr_draft_id=pr_draft_id,
            feedback_id=body.feedback_id,
            revised_patch_code=body.revised_patch_code,
            actor_id=actor_id
        )
        return rev
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pr-drafts/{pr_draft_id}/revisions", response_model=List[PatchRevisionResponse])
async def list_revisions_endpoint(
    pr_draft_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: Any = Depends(get_patch_revision_repository)
):
    """
    List all patch revisions for a Draft PR. Operator or Admin.
    """
    try:
        revisions = await repo.list_revisions_by_pr_draft(pr_draft_id)
        return revisions
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/revisions/{revision_id}/verify", response_model=PrVerificationResponse, status_code=status.HTTP_201_CREATED)
async def verify_revision_endpoint(
    revision_id: str,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_pr_verification_service)
):
    """
    Trigger Sandbox verification and PR Review Gate scoring for a specific patch revision. Admin-only.
    """
    actor_id = identity.get("id", "admin")
    try:
        verification = await service.verify_revision(revision_id=revision_id, actor_id=actor_id)
        return verification
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/pr-drafts/{pr_draft_id}/ai-suggestions", response_model=AIPatchSuggestionResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_patch_suggestion_endpoint(
    pr_draft_id: str,
    body: AIPatchSuggestionRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_ai_patch_suggestion_service),
):
    actor_id = identity.get("id", "admin")
    try:
        return await service.generate_suggestion(
            pr_draft_id=pr_draft_id,
            feedback_id=body.feedback_id,
            revision_id=body.revision_id,
            instruction=body.instruction,
            actor_id=actor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pr-drafts/{pr_draft_id}/ai-suggestions", response_model=List[AIPatchSuggestionResponse])
async def list_ai_patch_suggestions_endpoint(
    pr_draft_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    service: Any = Depends(get_ai_patch_suggestion_service),
):
    try:
        return await service.list_suggestions(pr_draft_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/ai-suggestions/{suggestion_id}", response_model=AIPatchSuggestionResponse)
async def get_ai_patch_suggestion_endpoint(
    suggestion_id: str,
    _identity: dict = Depends(require_permission("bilgeapi.operator")),
    repo: Any = Depends(get_ai_patch_suggestion_repository),
):
    suggestion = await repo.get_suggestion(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Patch Suggestion not found")
    return suggestion


@router.post("/ai-suggestions/{suggestion_id}/verify", response_model=PrVerificationResponse, status_code=status.HTTP_201_CREATED)
async def verify_ai_patch_suggestion_endpoint(
    suggestion_id: str,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_ai_patch_suggestion_service),
):
    actor_id = identity.get("id", "admin")
    try:
        return await service.verify_suggestion(suggestion_id, actor_id=actor_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/ai-suggestions/{suggestion_id}/accept-for-review", response_model=AIPatchSuggestionDecisionResponse)
async def accept_ai_patch_suggestion_endpoint(
    suggestion_id: str,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_ai_patch_suggestion_service),
):
    actor_id = identity.get("id", "admin")
    try:
        updated = await service.accept_for_review(suggestion_id, actor_id=actor_id)
        return AIPatchSuggestionDecisionResponse(
            id=updated["id"],
            status=updated["status"],
            reason=None,
            updated_at=updated["updated_at"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/ai-suggestions/{suggestion_id}/reject", response_model=AIPatchSuggestionDecisionResponse)
async def reject_ai_patch_suggestion_endpoint(
    suggestion_id: str,
    body: AIPatchSuggestionDecisionRequest,
    identity: dict = Depends(require_permission("bilgeapi.admin")),
    service: Any = Depends(get_ai_patch_suggestion_service),
):
    actor_id = identity.get("id", "admin")
    try:
        updated = await service.reject_suggestion(suggestion_id, reason=body.reason, actor_id=actor_id)
        return AIPatchSuggestionDecisionResponse(
            id=updated["id"],
            status=updated["status"],
            reason=body.reason,
            updated_at=updated["updated_at"],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


