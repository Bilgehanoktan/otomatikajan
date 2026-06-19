from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ProjectFactoryIntake(BaseModel):
    project_id: str
    source_suggestion_id: str
    audit_run_id: str
    title: str
    problem_statement: str
    recommended_action: str
    affected_files: List[str] = []
    suggested_scope: str = "mvp"
    status: str = "REQUIREMENT_GATE_WAITING"
    requires_operator_approval: bool = True

class RequirementGate(BaseModel):
    gate: str = "Requirement Approval Gate"
    status: str = "WAITING_FOR_OPERATOR"
    allowed_actions: List[str] = ["approve_scope", "request_revision", "reject"]
    implementation_allowed: bool = False
    sandbox_ready: bool = False
    approved_by: Optional[str] = None
    rationale: Optional[str] = None
    resolved_at: Optional[str] = None
    scope_adjustments: Optional[str] = None

class ApproveScopeRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    approved_scope: str = "mvp"
    risk_acknowledgement: bool = False

class RequestRevisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    revision_notes: str = Field(..., min_length=1)

class RejectRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)

class TaskItem(BaseModel):
    task_id: str
    description: str
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED
    estimated_minutes: int = 15

class ImplementationStartRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    runner_mode: str = "template_first"
    risk_acknowledgement: bool = False

class QualityScorecard(BaseModel):
    score: int
    checks: List[Dict[str, str]] = []

class RiskAssessment(BaseModel):
    risk_score: int
    risk_level: str
    blocking_risks: List[str] = []
    warnings: List[str] = []

class CandidateReview(BaseModel):
    project_id: str
    candidate_id: str
    status: str
    summary: str
    files_reviewed: List[str] = []
    quality_score: int
    risk_score: int
    security_findings: List[str] = []
    test_summary: Dict[str, Any]
    known_limitations: List[str] = []
    recommended_decision: str

class ApproveDeliveryRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks")

class RevisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    revision_notes: str = Field(..., min_length=1)

class RejectCandidateRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)

class ApplyPreviewRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks")

class DraftPrPrepareRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    target_branch: str = "main"
    draft_title: str = "Project Factory Candidate Delivery"
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks")

class FileChange(BaseModel):
    path: str
    change_type: str
    risk: str
    source_hash: str
    target_exists: bool

class ApplyPreview(BaseModel):
    project_id: str
    status: str = "APPLY_PREVIEW_READY"
    production_apply_performed: bool = False
    source_delivery_package: str = "delivery_package"
    file_changes: List[FileChange] = []
    conflicts: List[str] = []
    blocking_risks: List[str] = []
    summary: Dict[str, int] = {"add": 0, "modify": 0, "delete": 0}

class DraftPrPlan(BaseModel):
    project_id: str
    status: str = "DRAFT_PR_PLAN_READY"
    branch_name: str
    target_branch: str = "main"
    draft_title: str
    draft_body: str
    files_to_apply: List[str] = []
    apply_preview_ref: str = "apply_preview.json"
    requires_operator_confirmation: bool = True
    git_operations_performed: bool = False

class DraftPrCreateRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks")
    remote: str = "origin"

class DraftPrCreation(BaseModel):
    project_id: str
    status: str
    branch_name: str
    target_branch: str = "main"
    commit_sha: str = ""
    pr_url: str = ""
    is_draft: bool = True
    merge_performed: bool = False
    force_push_performed: bool = False
    production_direct_write: bool = False

# --- Phase 11: PR Review Gate Models ---

class PrReviewRunRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks")
    review_mode: str = "draft_pr_or_local_candidate"

class PrReviewDecisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    decision: str = Field(..., description="REQUEST_CHANGES | MARK_REVIEWED | BLOCK | DEFER")
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks")

class PrAgentFinding(BaseModel):
    category: str
    severity: str  # "blocking", "warning", "info"
    description: str
    file_path: Optional[str] = None

class PrAgentReview(BaseModel):
    status: str  # "PASSED", "BLOCKED", "WARNINGS"
    summary: str
    findings: List[PrAgentFinding] = []
    suggestions: List[str] = []

class VerifierCheck(BaseModel):
    name: str
    status: str  # "PASSED", "FAILED", "SKIPPED", "ERROR"
    detail: str = ""

class VerifierMeshReport(BaseModel):
    status: str  # "PASSED", "FAILED"
    checks: List[VerifierCheck] = []

class PrReviewScorecard(BaseModel):
    risk_score: int = 0
    quality_score: int = 100
    blocking_count: int = 0
    warning_count: int = 0
    verifier_pass_rate: float = 1.0

class PrReviewReport(BaseModel):
    project_id: str
    status: str  # PR_REVIEW_PASSED, PR_REVIEW_BLOCKED
    review_mode: str = "draft_pr_or_local_candidate"
    pr_url: str = ""
    fallback_mode: bool = False
    risk_score: int = 0
    quality_score: int = 100
    blocking_findings: List[str] = []
    warnings: List[str] = []
    recommended_decision: str = "MARK_REVIEWED"
    requires_operator_decision: bool = True

# --- Phase 12: Final Operator Decision + Release Archive Models ---

class FinalApproveRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks")

class FinalRejectRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)

class FinalRevisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    revision_notes: str = Field(..., min_length=1)

class FinalOperatorDecision(BaseModel):
    project_id: str
    decision: str  # FINAL_APPROVED, FINAL_REJECTED, FINAL_REVISION_REQUESTED
    operator_id: str
    rationale: str
    risk_acknowledgement: bool = False
    revision_notes: Optional[str] = None
    release_id: Optional[str] = None

class ReleaseManifest(BaseModel):
    project_id: str
    release_id: str
    status: str = "RELEASE_ARCHIVE_READY"
    final_decision: str = "FINAL_APPROVED"
    approved_by: str = ""
    production_apply_performed: bool = False
    merge_performed: bool = False
    deploy_performed: bool = False
    evidence_count: int = 0
    closure_report: str = "closure_report.md"

# --- Phase 13: Archive Index + Portfolio View Models ---

class ProjectIndexEntry(BaseModel):
    project_id: str
    title: str
    status: str
    release_id: Optional[str] = None
    final_decision: Optional[str] = None
    risk_level: Optional[str] = None
    quality_score: Optional[int] = None
    risk_score: Optional[int] = None
    release_archive_path: Optional[str] = None
    detail_url: str
    created_at: str
    updated_at: str

class ArchiveIndex(BaseModel):
    generated_at: str
    total_projects: int = 0
    closed_projects: int = 0
    active_projects: int = 0
    blocked_projects: int = 0
    revision_requested: int = 0
    projects: List[ProjectIndexEntry] = []

class PortfolioMetrics(BaseModel):
    total_projects: int = 0
    by_status: Dict[str, int] = {}
    by_risk_level: Dict[str, int] = {}
    average_quality_score: float = 0.0
    average_risk_score: float = 0.0
    release_archive_count: int = 0
    open_human_gates: int = 0
    blocked_count: int = 0

class RebuildArchiveRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)

# --- Phase 14: Portfolio Intelligence + Learning Memory Feedback Models ---

class RiskPattern(BaseModel):
    pattern: str
    count: int
    severity: str
    affected_projects: List[str] = []
    recommended_action: str
    suggested_workflow: Optional[str] = None

class TemplatePerformance(BaseModel):
    template: str
    uses: int
    success_rate: float
    average_quality_score: float
    average_risk_score: float

class AgentPerformance(BaseModel):
    agent: str
    uses: int
    success_rate: float
    blocked_count: int
    common_failure_modes: List[str] = []

class LearningRecommendation(BaseModel):
    recommendation_id: str
    title: str
    priority: str
    target: str
    suggested_workflow: str

class PortfolioIntelligence(BaseModel):
    generated_at: str
    source_index: str = "archive_index.json"
    portfolio_size: int = 0
    closed_projects: int = 0
    blocked_projects: int = 0
    average_quality_score: float = 0.0
    average_risk_score: float = 0.0
    recurring_risks: List[RiskPattern] = []
    template_performance: List[TemplatePerformance] = []
    agent_performance: List[AgentPerformance] = []
    learning_recommendations: List[LearningRecommendation] = []

class LearningSignal(BaseModel):
    signal_id: str
    type: str
    summary: str
    confidence: float
    recommended_policy_update: bool
    target_files: List[str] = []

class LearningNextAction(BaseModel):
    type: str
    title: str
    priority: str

class LearningMemoryFeedback(BaseModel):
    generated_at: str
    source: str = "project_factory_portfolio"
    signals: List[LearningSignal] = []
    next_actions: List[LearningNextAction] = []

class RunIntelligenceRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)

class CEOSuggestion(BaseModel):
    suggestion_id: str
    title: str
    description: str
    priority: str
    source: str = "portfolio_intelligence"

class CEOSuggestionsPublishRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)

# --- Phase 15: Portfolio Policy Autopilot Models ---

class RecommendedChange(BaseModel):
    field: str
    add: Optional[List[str]] = None
    remove: Optional[List[str]] = None
    update: Optional[Dict[str, Any]] = None

class PolicyProposal(BaseModel):
    proposal_id: str
    title: str
    description: str
    target_files: List[str]
    proposal_type: str  # "policy_hardening", "allowlist_update", etc.
    risk_level: str     # "LOW", "MEDIUM", "HIGH"
    priority: str       # "LOW", "MEDIUM", "HIGH"
    recommended_changes: List[RecommendedChange]
    status: str         # e.g., "POLICY_PROPOSAL_DRAFTED", "POLICY_PROPOSAL_APPROVED_FOR_BOARD", etc.
    requires_human_gate: bool = True
    auto_apply_allowed: bool = False

class PolicyProposalCollection(BaseModel):
    generated_at: str
    source: str = "portfolio_intelligence"
    proposals: List[PolicyProposal] = []

class PolicyImpactAnalysis(BaseModel):
    proposal_id: str
    target_files: List[str]
    affected_agents: List[str]
    expected_benefit: str
    potential_side_effects: List[str]
    rollback_plan_required: bool = True

class PolicyRiskAssessment(BaseModel):
    proposal_id: str
    risk_score: int
    risk_level: str
    blocking_risks: List[str] = []
    warnings: List[str] = []
    recommended_decision: str  # "APPROVE_FOR_POLICY_BOARD", "REJECT", "DEFER"

class RunPolicyAutopilotRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)

class PolicyProposalDecisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(False, description="Must acknowledge risks to approve for board")

# --- Phase 16: Policy Board Decision & Apply Preview Models ---

class PolicyBoardDecisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = False
    revision_notes: Optional[str] = None

class PreviewChange(BaseModel):
    target_file: str
    change_type: str  # "MODIFY", "ADD"
    field: str
    add: Optional[List[str]] = None
    remove: Optional[List[str]] = None
    update: Optional[Dict[str, Any]] = None
    risk: str

class PolicyApplyPreview(BaseModel):
    proposal_id: str
    status: str = "POLICY_APPLY_PREVIEW_READY"
    production_apply_performed: bool = False
    policy_files_modified: bool = False
    target_files: List[str]
    preview_changes: List[PreviewChange]
    blocking_risks: List[str] = []
    warnings: List[str] = []

class PolicyBoardPackage(BaseModel):
    status: str = "POLICY_BOARD_PACKAGE_READY"
    proposal_count: int
    approved_for_preview: int
    preview_ready: int
    blocked: int
    package_refs: Dict[str, str] = {
        "policy_proposals": "policy_proposals.json",
        "impact_analysis": "policy_impact_analysis.json",
        "risk_assessment": "policy_risk_assessment.json",
        "apply_preview": "policy_apply_preview.json",
        "diff_summary": "policy_diff_summary.md"
    }
    next_step: str = "policy_draft_pr_plan"

# --- Phase 17: Policy Draft PR Plan & Governance Evidence Models ---

class PolicyDraftPRPlanRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    target_branch: str = Field("main", min_length=1)
    draft_title: str = Field(..., min_length=5)
    risk_acknowledgement: bool = False

class PolicyDraftPRPlan(BaseModel):
    proposal_id: str
    status: str = "POLICY_DRAFT_PR_PLAN_READY"
    branch_name: str
    target_branch: str
    draft_title: str
    draft_body: str
    files_to_apply: List[str]
    apply_preview_ref: str = "policy_apply_preview.json"
    governance_evidence_ref: str = "policy_governance_evidence_pack"
    requires_operator_confirmation: bool = True
    git_operations_performed: bool = False
    policy_files_modified: bool = False

class PolicyPRCreationRequest(BaseModel):
    operator_id: str
    rationale: str
    risk_acknowledgement: bool
    remote: str = "origin"
    mode: str = "safe_local_or_mock"

class PolicyPRCreationResult(BaseModel):
    proposal_id: str
    status: str
    branch_name: str
    target_branch: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_url: Optional[str] = None
    is_draft: bool = True
    merge_performed: bool = False
    force_push_performed: bool = False
    production_direct_write: bool = False
    policy_files_modified: bool = False
    modified_files: List[str] = Field(default_factory=list)
    four_eyes_enforced: bool = False
    reason: Optional[str] = None

class PolicyGovernanceManifest(BaseModel):
    status: str = "POLICY_GOVERNANCE_EVIDENCE_READY"
    proposal_id: str
    evidence_count: int
    source: str = "policy_autopilot"
    production_apply_performed: bool = False
    policy_files_modified: bool = False
    git_operations_performed: bool = False
    ready_for_operator_pr_creation: bool = True

# --- Phase 19: Policy PR Review Gate + Verifier Mesh Models ---

class PolicyPRReviewRunRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks to run review")

class PolicyPRReviewDecisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    decision: str = Field(..., description="MARK_REVIEWED | REQUEST_CHANGES | BLOCK | DEFER")
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = Field(..., description="Must acknowledge risks")

class PolicyPRReviewScorecard(BaseModel):
    risk_score: int = 0
    quality_score: int = 100
    blocking_count: int = 0
    warning_count: int = 0
    verifier_pass_rate: float = 1.0

class PolicyVerifierCheck(BaseModel):
    name: str
    status: str  # "PASSED", "FAILED"
    detail: str = ""

class PolicyVerifierMeshReport(BaseModel):
    proposal_id: str
    status: str  # "PASSED", "FAILED"
    checks: List[PolicyVerifierCheck] = []

class PolicyPRAgentReview(BaseModel):
    proposal_id: str
    status: str  # "PASSED", "WARNINGS", "BLOCKED"
    summary: str
    findings: List[Dict[str, str]] = []  # category, severity, description
    suggestions: List[str] = []

class PolicyPRReviewReport(BaseModel):
    proposal_id: str
    status: str  # POLICY_PR_REVIEW_PASSED, POLICY_PR_REVIEW_BLOCKED, etc.
    pr_url: str = ""
    fallback_mode: bool = False
    risk_score: int = 0
    quality_score: int = 100
    blocking_findings: List[str] = []
    warnings: List[str] = []
    recommended_decision: str = "MARK_REVIEWED"
    requires_operator_decision: bool = True

# --- Phase 20: Policy Final Decision + Release Archive Models ---

class PolicyFinalDecisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    risk_acknowledgement: bool = False

class PolicyFinalRevisionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=5)
    revision_notes: str = Field(..., min_length=1)

class PolicyReleaseManifest(BaseModel):
    proposal_id: str
    release_id: str
    status: str = "POLICY_RELEASE_ARCHIVE_READY"
    final_decision: str = "FINAL_POLICY_APPROVED"
    approved_by: str = ""
    production_apply_performed: bool = False
    policy_files_modified: bool = False
    merge_performed: bool = False
    deploy_performed: bool = False
    learning_memory_synced: bool = False
    evidence_count: int = 0

class PolicyLearningSignal(BaseModel):
    type: str
    summary: str
    confidence: float
    target_files: List[str] = []

class PolicyLearningMemorySync(BaseModel):
    status: str = "POLICY_LEARNING_SYNCED"
    proposal_id: str
    source: str = "policy_autopilot_final_release"
    signals: List[PolicyLearningSignal] = []
    write_mode: str = "artifact_only"
    memory_files_modified: bool = False
