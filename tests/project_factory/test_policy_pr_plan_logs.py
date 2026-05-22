import os
import json
import pytest
from unittest.mock import patch
from services.project_factory.policy_pr_plan_logs import log_policy_pr_plan, load_policy_pr_plan_logs

@patch("services.project_factory.policy_pr_plan_logs._resolve_policy_autopilot_dir")
def test_policy_pr_plan_logs_append_only(mock_resolve, tmp_path):
    mock_resolve.return_value = tmp_path
    
    log_policy_pr_plan(
        action="PREPARE_POLICY_DRAFT_PR_PLAN",
        proposal_id="POL-1",
        operator_id="OP-1",
        rationale="first",
        status="POLICY_DRAFT_PR_PLAN_READY"
    )
    
    log_policy_pr_plan(
        action="PREPARE_POLICY_DRAFT_PR_PLAN_BLOCKED",
        proposal_id="POL-2",
        operator_id="OP-1",
        rationale="second",
        status="POLICY_PR_PLAN_BLOCKED"
    )
    
    logs = load_policy_pr_plan_logs()
    assert len(logs) == 2
    assert logs[0]["proposal_id"] == "POL-1"
    assert logs[1]["proposal_id"] == "POL-2"
    assert logs[0]["git_operations_performed"] == False

