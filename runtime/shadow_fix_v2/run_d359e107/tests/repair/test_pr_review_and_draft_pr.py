import json
import pytest
from pathlib import Path
from services.repair.github_pr_adapter import prepare_draft_pr
from services.repair.taskflow_artifacts import artifact_dir_for_run

@pytest.fixture
def mock_run_setup(tmp_path):
    """
    Sets up a temporary taskflow run directory with standard artifacts.
    """
    incident_id = "INC-12345"
    run_id = "RUN-98765"
    
    # Taskflow run directory: tmp_path / incident_id / taskflow / run_id
    run_dir = tmp_path / incident_id / "taskflow" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Write standard taskflow_run.json
    (run_dir / "taskflow_run.json").write_text(
        json.dumps({"run_id": run_id, "status": "WAITING_HUMAN"}), encoding="utf-8"
    )
    
    # Write standard patch_candidates.json
    candidates = [
        {
            "candidate_id": "cand-001",
            "strategy": "safe_fix",
            "changed_files": ["src/auth.py"],
            "patch_diff": "diff --git a/src/auth.py b/src/auth.py\n..."
        },
        {
            "candidate_id": "cand-002",
            "strategy": "risky_fix",
            "changed_files": ["src/auth.py"],
            "patch_diff": "diff --git a/src/auth.py b/src/auth.py\n..."
        }
    ]
    (run_dir / "patch_candidates.json").write_text(json.dumps(candidates), encoding="utf-8")
    
    # Write standard sandbox_result.json
    sandbox = {
        "tests_passed": True,
        "status": "passed"
    }
    (run_dir / "sandbox_result.json").write_text(json.dumps(sandbox), encoding="utf-8")
    
    # Write standard verifier_mesh_result.json
    verifier = {
        "status": "passed",
        "verifier_passed": True
    }
    (run_dir / "verifier_mesh_result.json").write_text(json.dumps(verifier), encoding="utf-8")
    
    # Write standard human_gate_decision.json
    gate = {
        "status": "APPROVED",
        "selected_candidate_id": "cand-001",
        "decision": "approve_and_apply",
        "rationale": "Code looks very clean and secure.",
        "risk_score": 0.15,
        "risk_level": "LOW"
    }
    (run_dir / "human_gate_decision.json").write_text(json.dumps(gate), encoding="utf-8")
    
    # Write standard pr_review.json
    review = {
        "status": "completed",
        "review_passed": True,
        "confidence": 0.95,
        "findings": [],
        "blocking_comments": [],
        "suggested_improvements": []
    }
    (run_dir / "pr_review.json").write_text(json.dumps(review), encoding="utf-8")
    
    context = {
        "incident_id": incident_id,
        "run_id": run_id,
        "output_root": str(tmp_path)
    }
    return context, run_dir

def test_prepare_draft_pr_success(mock_run_setup):
    context, run_dir = mock_run_setup
    
    res = prepare_draft_pr(context)
    assert res["artifact_type"] == "json"
    
    # Verify metadata artifact is created
    metadata_path = run_dir / "draft_pr_metadata.json"
    assert metadata_path.exists()
    
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["status"] == "DRAFT_PR_READY"
    assert metadata["incident_id"] == "INC-12345"
    assert metadata["run_id"] == "RUN-98765"
    assert metadata["selected_candidate_id"] == "cand-001"
    assert metadata["human_gate_status"] == "APPROVED"
    assert metadata["risk_score"] == 0.15
    assert metadata["risk_level"] == "LOW"
    assert metadata["changed_files"] == ["src/auth.py"]
    
    # Check that taskflow_run.json status is updated
    run_json = json.loads((run_dir / "taskflow_run.json").read_text(encoding="utf-8"))
    assert run_json["status"] == "PR_DRAFTED"

def test_prepare_draft_pr_missing_human_gate(mock_run_setup):
    context, run_dir = mock_run_setup
    (run_dir / "human_gate_decision.json").unlink()
    
    with pytest.raises(ValueError, match="Human Gate Decision artifact is missing"):
        prepare_draft_pr(context)

def test_prepare_draft_pr_not_approved(mock_run_setup):
    context, run_dir = mock_run_setup
    # Change status to REJECTED
    gate = json.loads((run_dir / "human_gate_decision.json").read_text(encoding="utf-8"))
    gate["status"] = "REJECTED"
    (run_dir / "human_gate_decision.json").write_text(json.dumps(gate), encoding="utf-8")
    
    with pytest.raises(ValueError, match="blocks draft PR preparation"):
        prepare_draft_pr(context)

def test_prepare_draft_pr_missing_pr_review(mock_run_setup):
    context, run_dir = mock_run_setup
    (run_dir / "pr_review.json").unlink()
    
    with pytest.raises(ValueError, match="PR review artifact .* is missing"):
        prepare_draft_pr(context)

def test_prepare_draft_pr_pr_review_not_completed(mock_run_setup):
    context, run_dir = mock_run_setup
    review = json.loads((run_dir / "pr_review.json").read_text(encoding="utf-8"))
    review["status"] = "pending"
    (run_dir / "pr_review.json").write_text(json.dumps(review), encoding="utf-8")
    
    with pytest.raises(ValueError, match="is not completed"):
        prepare_draft_pr(context)

def test_prepare_draft_pr_blocking_comments_without_ack(mock_run_setup):
    context, run_dir = mock_run_setup
    review = json.loads((run_dir / "pr_review.json").read_text(encoding="utf-8"))
    review["blocking_comments"] = ["Avoid using unsafe memory patterns."]
    (run_dir / "pr_review.json").write_text(json.dumps(review), encoding="utf-8")
    
    with pytest.raises(ValueError, match="Active blocking comments exist in PR review"):
        prepare_draft_pr(context)

def test_prepare_draft_pr_blocking_comments_with_ack(mock_run_setup):
    context, run_dir = mock_run_setup
    review = json.loads((run_dir / "pr_review.json").read_text(encoding="utf-8"))
    review["blocking_comments"] = ["Avoid using unsafe memory patterns."]
    (run_dir / "pr_review.json").write_text(json.dumps(review), encoding="utf-8")
    
    context["operator_acknowledged_blocking_comments"] = True
    res = prepare_draft_pr(context)
    assert res["artifact_type"] == "json"

def test_prepare_draft_pr_selected_candidate_not_in_list(mock_run_setup):
    context, run_dir = mock_run_setup
    gate = json.loads((run_dir / "human_gate_decision.json").read_text(encoding="utf-8"))
    gate["selected_candidate_id"] = "cand-999"
    (run_dir / "human_gate_decision.json").write_text(json.dumps(gate), encoding="utf-8")
    
    with pytest.raises(ValueError, match="is not in patch candidates list"):
        prepare_draft_pr(context)

def test_prepare_draft_pr_sandbox_failed(mock_run_setup):
    context, run_dir = mock_run_setup
    sandbox = {
        "tests_passed": False,
        "status": "failed"
    }
    (run_dir / "sandbox_result.json").write_text(json.dumps(sandbox), encoding="utf-8")
    
    with pytest.raises(ValueError, match="Sandbox tests did not pass"):
        prepare_draft_pr(context)

def test_prepare_draft_pr_verifier_mesh_failed(mock_run_setup):
    context, run_dir = mock_run_setup
    verifier = {
        "status": "failed",
        "verifier_passed": False
    }
    (run_dir / "verifier_mesh_result.json").write_text(json.dumps(verifier), encoding="utf-8")
    
    with pytest.raises(ValueError, match="Verifier mesh status is"):
        prepare_draft_pr(context)
