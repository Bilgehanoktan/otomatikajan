import pytest
from services.project_factory.policy_pr_plan_safety import check_policy_pr_plan_safety

def test_check_policy_pr_plan_safety_success():
    apply_preview = {
        "production_apply_performed": False,
        "policy_files_modified": False,
        "blocking_risks": []
    }
    proposal = {
        "auto_apply_allowed": False,
        "target_files": ["configs/policy.yaml"]
    }
    
    risks = check_policy_pr_plan_safety(
        apply_preview=apply_preview,
        proposal=proposal,
        target_branch="main",
        branch_name="codex/policy-1",
        risk_acknowledgement=True
    )
    assert len(risks) == 0

def test_check_policy_pr_plan_safety_blocks():
    apply_preview = {
        "production_apply_performed": True, # BLOCK
        "policy_files_modified": True, # BLOCK
        "blocking_risks": ["Danger"] # BLOCK
    }
    proposal = {
        "auto_apply_allowed": True, # BLOCK
        "target_files": [".env"] # BLOCK
    }
    
    risks = check_policy_pr_plan_safety(
        apply_preview=apply_preview,
        proposal=proposal,
        target_branch="", # BLOCK
        branch_name="invalid-branch", # BLOCK
        risk_acknowledgement=False # BLOCK
    )
    
    assert len(risks) == 8
