from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.repositories.interface import ResearchRepository, ImprovementRepository
from apps.bilgeapi.services.research import WebResearchAdapter
from apps.bilgeapi.services.improvement import ImprovementProposalEngine, ReleaseGateSimulator
from apps.bilgeapi.schemas.improvements import (
    ResearchCreate, ResearchResponse, EvidenceResponse, ProposalResponse, DraftPrResponse
)
from apps.bilgeapi.routers.deps import (
    get_research_repository,
    get_improvement_repository,
    get_web_research_adapter,
    get_improvement_proposal_engine,
    get_release_gate_simulator
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

    return DraftPrResponse(
        patch_code=proposal["patch_code"],
        title=f"Draft PR: {proposal['title']}",
        description=f"Autonomous Self-Improvement patch.\n\n### Rationale:\n{proposal['rationale']}",
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
    """
    actor_id = identity.get("id", "admin")
    proposal = await repo.approve_proposal(
        proposal_id=proposal_id,
        approved_by=actor_id,
        approved_at=datetime.now(timezone.utc)
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal
