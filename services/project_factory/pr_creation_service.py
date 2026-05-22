from typing import Dict, Any, Optional
from services.project_factory.models import DraftPrCreateRequest, DraftPrCreation
from services.project_factory.artifacts import load_project_factory_artifacts, write_project_factory_artifacts, write_draft_pr_creation
from services.project_factory.pr_safety import validate_pr_creation_safety
from services.project_factory.git_workspace import GitWorkspaceExecutor, GitSafetyViolation
from services.project_factory.github_pr_adapter import create_draft_pr, GitHubRemoteUnavailable
from services.project_factory.pr_creation_logs import record_pr_creation_decision

def execute_pr_creation(
    project_id: str,
    req: DraftPrCreateRequest,
    workspace_root: Optional[str] = None
) -> DraftPrCreation:
    # 1. Update status to CREATING
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    brief.status = "DRAFT_PR_CREATING"
    gate.status = "DRAFT_PR_CREATING"
    write_project_factory_artifacts(brief, gate, workspace_root)

    creation_doc = DraftPrCreation(
        project_id=project_id,
        status="DRAFT_PR_CREATING",
        branch_name="",
        target_branch="main"
    )
    
    try:
        # 2. Safety Validation
        validation_data = validate_pr_creation_safety(
            project_id=project_id,
            operator_id=req.operator_id,
            rationale=req.rationale,
            risk_acknowledgement=req.risk_acknowledgement,
            workspace_root=workspace_root
        )
        pr_plan = validation_data["draft_pr_plan"]
        
        branch_name = pr_plan["branch_name"]
        creation_doc.branch_name = branch_name
        creation_doc.target_branch = pr_plan.get("target_branch", "main")
        
        # 3. Git Operations
        git_exec = GitWorkspaceExecutor(workspace_root=str(workspace_root) if workspace_root else ".")
        git_exec.create_and_checkout_branch(branch_name)
        
        files_to_apply = pr_plan.get("files_to_apply", [])
        git_exec.apply_delivery_files(project_id, files_to_apply)
        
        commit_sha = git_exec.commit_changes("feat: project factory candidate delivery")
        creation_doc.commit_sha = commit_sha
        
        git_exec.push_branch(req.remote, branch_name)
        
        # 4. GitHub PR Adapter
        title = pr_plan.get("draft_title", "Draft PR")
        body = pr_plan.get("draft_body", "")
        
        try:
            pr_url, status = create_draft_pr(
                title=title,
                body=body,
                head_branch=branch_name,
                base_branch=creation_doc.target_branch
            )
            creation_doc.pr_url = pr_url
            creation_doc.status = "PR_CREATED_WAITING_REVIEW"
        except GitHubRemoteUnavailable as ghe:
            creation_doc.status = "PR_CREATION_BLOCKED"
            record_pr_creation_decision(
                project_id=project_id,
                action="GITHUB_REMOTE_UNAVAILABLE",
                operator_id=req.operator_id,
                rationale=str(ghe),
                workspace_root=workspace_root
            )
        
    except (ValueError, GitSafetyViolation, RuntimeError) as e:
        creation_doc.status = "DRAFT_PR_FAILED"
        brief.status = "DRAFT_PR_FAILED"
        gate.status = "DRAFT_PR_FAILED"
        write_project_factory_artifacts(brief, gate, workspace_root)
        write_draft_pr_creation(project_id, creation_doc.model_dump(), workspace_root)
        
        record_pr_creation_decision(
            project_id=project_id,
            action="PR_CREATION_FAILED",
            operator_id=req.operator_id,
            rationale=str(e),
            workspace_root=workspace_root
        )
        raise e

    # 5. Commit state transitions
    brief.status = creation_doc.status
    gate.status = creation_doc.status
    write_project_factory_artifacts(brief, gate, workspace_root)
    write_draft_pr_creation(project_id, creation_doc.model_dump(), workspace_root)
    
    record_pr_creation_decision(
        project_id=project_id,
        action="CREATE_DRAFT_PR",
        operator_id=req.operator_id,
        rationale=req.rationale,
        details=creation_doc.model_dump(),
        workspace_root=workspace_root
    )

    return creation_doc

def abort_pr_creation(
    project_id: str,
    operator_id: str,
    rationale: str,
    workspace_root: Optional[str] = None
) -> DraftPrCreation:
    """
    Aborts a pending or failed PR creation back to an ABORTED state.
    """
    brief, gate = load_project_factory_artifacts(project_id, workspace_root)
    
    valid_states = ["DRAFT_PR_WAITING_APPROVAL", "DRAFT_PR_FAILED"]
    if gate.status not in valid_states:
        raise ValueError(f"Cannot abort PR creation from state {gate.status}.")
        
    brief.status = "DRAFT_PR_ABORTED"
    gate.status = "DRAFT_PR_ABORTED"
    write_project_factory_artifacts(brief, gate, workspace_root)
    
    creation_doc = DraftPrCreation(
        project_id=project_id,
        status="DRAFT_PR_ABORTED",
        branch_name="",
        target_branch="main"
    )
    write_draft_pr_creation(project_id, creation_doc.model_dump(), workspace_root)
    
    record_pr_creation_decision(
        project_id=project_id,
        action="ABORT_PR_CREATION",
        operator_id=operator_id,
        rationale=rationale,
        workspace_root=workspace_root
    )
    
    return creation_doc
