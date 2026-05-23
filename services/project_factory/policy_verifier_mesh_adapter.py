from typing import Dict, Any, List
from services.project_factory.models import PolicyVerifierMeshReport, PolicyVerifierCheck
from services.project_factory.artifacts import (
    load_policy_pr_creation,
    load_policy_apply_preview,
    load_policy_governance_manifest,
    load_policy_draft_pr_plan,
    write_policy_verifier_mesh_report
)

def run_policy_verifier_mesh(proposal_id: str, workspace_root: str = None) -> PolicyVerifierMeshReport:
    """
    Runs safety constraints and verifies PR properties.
    """
    pr_creation = load_policy_pr_creation(proposal_id, workspace_root) or {}
    apply_preview = load_policy_apply_preview(proposal_id, workspace_root) or {}
    gov_manifest = load_policy_governance_manifest(proposal_id, workspace_root) or {}
    pr_plan = load_policy_draft_pr_plan(proposal_id, workspace_root) or {}

    checks: List[PolicyVerifierCheck] = []
    
    # 1. merge_performed = False
    c_merge = pr_creation.get("merge_performed", False)
    checks.append(PolicyVerifierCheck(
        name="pr_creation_merge_performed",
        status="FAILED" if c_merge else "PASSED",
        detail=f"merge_performed: {c_merge}"
    ))

    # 2. force_push_performed = False
    c_force = pr_creation.get("force_push_performed", False)
    checks.append(PolicyVerifierCheck(
        name="pr_creation_force_push",
        status="FAILED" if c_force else "PASSED",
        detail=f"force_push_performed: {c_force}"
    ))

    # 3. production_direct_write = False
    c_pdw = pr_creation.get("production_direct_write", False)
    checks.append(PolicyVerifierCheck(
        name="pr_creation_direct_write",
        status="FAILED" if c_pdw else "PASSED",
        detail=f"production_direct_write: {c_pdw}"
    ))

    # 4. is_draft = True
    c_draft = pr_creation.get("is_draft", False)
    checks.append(PolicyVerifierCheck(
        name="pr_creation_is_draft",
        status="PASSED" if c_draft else "FAILED",
        detail=f"is_draft: {c_draft}"
    ))

    # 5. branch_name starts with codex/
    b_name = pr_creation.get("branch_name", "")
    checks.append(PolicyVerifierCheck(
        name="pr_creation_branch_prefix",
        status="PASSED" if b_name.startswith("codex/") else "FAILED",
        detail=f"branch_name: {b_name}"
    ))

    # 6. apply_preview.production_apply_performed = False
    ap_pdw = apply_preview.get("production_apply_performed", False)
    checks.append(PolicyVerifierCheck(
        name="apply_preview_direct_write",
        status="FAILED" if ap_pdw else "PASSED",
        detail=f"production_apply_performed: {ap_pdw}"
    ))

    # 7. governance_manifest.git_operations_performed = False
    # (Actually logged in draft_pr_plan in Phase 17, but let's check both just in case)
    gov_git = gov_manifest.get("git_operations_performed", False)
    plan_git = pr_plan.get("git_operations_performed", False)
    checks.append(PolicyVerifierCheck(
        name="pre_pr_git_operations",
        status="FAILED" if (gov_git or plan_git) else "PASSED",
        detail=f"gov_git: {gov_git}, plan_git: {plan_git}"
    ))

    # 8. Files changed are within allowed target files and no forbidden files
    allowed_files = set(pr_plan.get("files_to_apply", []))
    modified_files = set(pr_creation.get("modified_files", []))
    
    forbidden_keywords = [".env", "secret", "db"]
    has_forbidden = any(any(kw in f for kw in forbidden_keywords) for f in modified_files)
    is_subset = modified_files.issubset(allowed_files)

    checks.append(PolicyVerifierCheck(
        name="modified_files_scope",
        status="FAILED" if has_forbidden or not is_subset else "PASSED",
        detail=f"forbidden: {has_forbidden}, subset: {is_subset}, modified: {modified_files}, allowed: {allowed_files}"
    ))

    overall_status = "PASSED"
    if any(c.status == "FAILED" for c in checks):
        overall_status = "FAILED"
        
    report = PolicyVerifierMeshReport(
        proposal_id=proposal_id,
        status=overall_status,
        checks=checks
    )
    
    write_policy_verifier_mesh_report(proposal_id, report.model_dump(), workspace_root)
    return report
