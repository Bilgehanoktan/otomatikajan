import pytest
from unittest.mock import patch, MagicMock
from services.project_factory.policy_governance_packager import generate_governance_evidence_pack

@patch("services.project_factory.policy_governance_packager.load_policy_draft_pr_plan")
@patch("services.project_factory.policy_governance_packager.load_policy_apply_preview")
@patch("services.project_factory.policy_governance_packager._resolve_policy_autopilot_dir")
@patch("services.project_factory.policy_governance_packager.write_policy_governance_manifest")
@patch("services.project_factory.policy_governance_packager.shutil.copy2")
def test_generate_governance_evidence_pack(mock_copy, mock_write, mock_resolve, mock_preview, mock_plan):
    mock_plan.return_value = {"proposal_id": "POL-1", "branch_name": "codex/test", "target_branch": "main"}
    mock_preview.return_value = {"proposal_id": "POL-1", "production_apply_performed": False}
    
    mock_dir = MagicMock()
    mock_dir.__truediv__.return_value = mock_dir
    mock_dir.exists.return_value = True
    mock_resolve.return_value = mock_dir
    
    res = generate_governance_evidence_pack("POL-1", "root")
    
    assert res["status"] == "POLICY_GOVERNANCE_EVIDENCE_READY"
    assert res["proposal_id"] == "POL-1"
    assert res["git_operations_performed"] == False
    assert res["policy_files_modified"] == False
    assert res["production_apply_performed"] == False
    
    # 8 files to copy
    assert mock_copy.call_count == 8
    mock_write.assert_called_once()
