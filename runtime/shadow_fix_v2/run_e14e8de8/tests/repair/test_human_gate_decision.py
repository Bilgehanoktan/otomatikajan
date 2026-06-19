import json
import pytest
from pathlib import Path
from services.repair.human_gate import (
    HumanGateDecisionRequest,
    HumanGateDecisionType,
    HumanGateStatus,
    record_human_gate_decision
)

@pytest.fixture
def mock_run_env(tmp_path):
    # Create incident / taskflow structure
    incident_id = "INC-12345"
    run_id = "RUN-99999"
    run_dir = tmp_path / incident_id / "taskflow" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Write mock human_gate_decision.json
    gate_payload = {
        "status": "WAITING_FOR_OPERATOR",
        "incident_id": incident_id,
        "run_id": run_id,
        "risk_score": 0.61,
        "risk_threshold": 0.30,
        "waiting_reason": "Risk 0.61 > threshold 0.30",
        "candidate_ids": ["candidate-001"],
        "required_decision_fields": [
            "operator_id",
            "decision",
            "rationale",
            "selected_candidate_id",
            "risk_acknowledgement",
            "rollback_required"
        ],
        "artifact_refs": {
            "risk_report": "...",
            "patch_candidates": "...",
            "verifier_mesh_result": "...",
            "sandbox_result": "..."
        }
    }
    (run_dir / "human_gate_decision.json").write_text(json.dumps(gate_payload), encoding="utf-8")
    
    # Write mock patch_candidates.json
    candidates_payload = [
        {
            "candidate_id": "candidate-001",
            "policy_status": "allowed",
            "status": "allowed",
            "changed_files": ["src/main.py"]
        },
        {
            "candidate_id": "candidate-002",
            "policy_status": "denied",
            "status": "denied",
            "changed_files": ["src/denied.py"]
        }
    ]
    (run_dir / "patch_candidates.json").write_text(json.dumps(candidates_payload), encoding="utf-8")
    
    # Write mock sandbox_result.json
    sandbox_payload = {
        "candidate-001": {"tests_passed": True},
        "candidate-002": {"tests_passed": True},
        "candidate-003": {"tests_passed": False}
    }
    (run_dir / "sandbox_result.json").write_text(json.dumps(sandbox_payload), encoding="utf-8")
    
    # Write mock verifier_mesh_result.json
    verifier_payload = {
        "verifier_status": "passed",
        "results": []
    }
    (run_dir / "verifier_mesh_result.json").write_text(json.dumps(verifier_payload), encoding="utf-8")
    
    return tmp_path, incident_id, run_id, run_dir

def test_human_gate_requires_operator_rationale(mock_run_env):
    tmp_path, incident_id, run_id, run_dir = mock_run_env
    req = HumanGateDecisionRequest(
        operator_id="operator-001",
        decision=HumanGateDecisionType.OPEN_DRAFT_PR_ONLY,
        rationale="",
        selected_candidate_id="candidate-001",
        risk_acknowledgement=True,
        rollback_required=False
    )
    with pytest.raises(ValueError, match="Operator rationale cannot be empty"):
        record_human_gate_decision(incident_id, run_id, req, output_root=tmp_path)

def test_human_gate_rejects_unknown_candidate(mock_run_env):
    tmp_path, incident_id, run_id, run_dir = mock_run_env
    req = HumanGateDecisionRequest(
        operator_id="operator-001",
        decision=HumanGateDecisionType.OPEN_DRAFT_PR_ONLY,
        rationale="Verifier passed but risk is above automatic apply threshold.",
        selected_candidate_id="candidate-999",
        risk_acknowledgement=True,
        rollback_required=False
    )
    with pytest.raises(ValueError, match="is not in the allowed list"):
        record_human_gate_decision(incident_id, run_id, req, output_root=tmp_path)

def test_human_gate_requires_risk_acknowledgement_for_high_risk(mock_run_env):
    tmp_path, incident_id, run_id, run_dir = mock_run_env
    req = HumanGateDecisionRequest(
        operator_id="operator-001",
        decision=HumanGateDecisionType.OPEN_DRAFT_PR_ONLY,
        rationale="Verifier passed.",
        selected_candidate_id="candidate-001",
        risk_acknowledgement=False,
        rollback_required=False
    )
    with pytest.raises(ValueError, match="Risk acknowledgement is required"):
        record_human_gate_decision(incident_id, run_id, req, output_root=tmp_path)

def test_human_gate_requires_rollback_ref_when_rollback_required(mock_run_env):
    tmp_path, incident_id, run_id, run_dir = mock_run_env
    req = HumanGateDecisionRequest(
        operator_id="operator-001",
        decision=HumanGateDecisionType.OPEN_DRAFT_PR_ONLY,
        rationale="Verifier passed.",
        selected_candidate_id="candidate-001",
        risk_acknowledgement=True,
        rollback_required=True,
        rollback_plan_ref=None
    )
    with pytest.raises(ValueError, match="Rollback plan reference is required"):
        record_human_gate_decision(incident_id, run_id, req, output_root=tmp_path)

def test_policy_denied_candidate_cannot_be_approved(mock_run_env):
    tmp_path, incident_id, run_id, run_dir = mock_run_env
    # Add candidate-002 to allowed list in gate first
    gate_path = run_dir / "human_gate_decision.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    gate["candidate_ids"].append("candidate-002")
    gate_path.write_text(json.dumps(gate), encoding="utf-8")
    
    req = HumanGateDecisionRequest(
        operator_id="operator-001",
        decision=HumanGateDecisionType.APPROVE_CONSERVATIVE_PATCH,
        rationale="Let's push it anyway.",
        selected_candidate_id="candidate-002",
        risk_acknowledgement=True,
        rollback_required=False
    )
    with pytest.raises(ValueError, match="policy status is DENIED"):
        record_human_gate_decision(incident_id, run_id, req, output_root=tmp_path)

def test_sandbox_failed_candidate_cannot_be_approved(mock_run_env):
    tmp_path, incident_id, run_id, run_dir = mock_run_env
    # Add candidate-003 to allowed list in gate first
    gate_path = run_dir / "human_gate_decision.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    gate["candidate_ids"].append("candidate-003")
    gate_path.write_text(json.dumps(gate), encoding="utf-8")
    
    # Also add details in patch_candidates.json
    candidates_path = run_dir / "patch_candidates.json"
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    candidates.append({
        "candidate_id": "candidate-003",
        "policy_status": "allowed",
        "status": "allowed",
        "changed_files": []
    })
    candidates_path.write_text(json.dumps(candidates), encoding="utf-8")
    
    req = HumanGateDecisionRequest(
        operator_id="operator-001",
        decision=HumanGateDecisionType.APPROVE_CONSERVATIVE_PATCH,
        rationale="Let's push sandbox failed.",
        selected_candidate_id="candidate-003",
        risk_acknowledgement=True,
        rollback_required=False
    )
    with pytest.raises(ValueError, match="sandbox tests failed"):
        record_human_gate_decision(incident_id, run_id, req, output_root=tmp_path)

def test_valid_open_draft_pr_only_decision_updates_gate_artifact(mock_run_env):
    tmp_path, incident_id, run_id, run_dir = mock_run_env
    req = HumanGateDecisionRequest(
        operator_id="operator-001",
        decision=HumanGateDecisionType.OPEN_DRAFT_PR_ONLY,
        rationale="Verifier passed but risk is above automatic apply threshold.",
        selected_candidate_id="candidate-001",
        risk_acknowledgement=True,
        rollback_required=True,
        rollback_plan_ref="repair_outputs/INC-12345/rollback_plan.json"
    )
    res = record_human_gate_decision(incident_id, run_id, req, output_root=tmp_path)
    assert res["status"] == "DRAFT_PR_ONLY"
    assert res["operator_id"] == "operator-001"
    assert res["decision"] == "open_draft_pr_only"
    assert res["selected_candidate_id"] == "candidate-001"
    
    # Read gate file
    gate_path = run_dir / "human_gate_decision.json"
    gate_data = json.loads(gate_path.read_text(encoding="utf-8"))
    assert gate_data["status"] == "DRAFT_PR_ONLY"
    assert gate_data["rollback_plan_ref"] == "repair_outputs/INC-12345/rollback_plan.json"

def test_human_gate_decision_appends_audit_log(mock_run_env):
    tmp_path, incident_id, run_id, run_dir = mock_run_env
    req = HumanGateDecisionRequest(
        operator_id="operator-002",
        decision=HumanGateDecisionType.APPROVE_CONSERVATIVE_PATCH,
        rationale="Clean and elegant candidate.",
        selected_candidate_id="candidate-001",
        risk_acknowledgement=True,
        rollback_required=False
    )
    res = record_human_gate_decision(incident_id, run_id, req, output_root=tmp_path)
    assert res["status"] == "APPROVED"
    
    # Check audit log
    audit_path = run_dir / "human_gate_audit.jsonl"
    assert audit_path.exists()
    lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    log = json.loads(lines[0])
    assert log["event"] == "human_gate_decision_recorded"
    assert log["operator_id"] == "operator-002"
    assert log["decision"] == "approve_conservative_patch"
    assert log["selected_candidate_id"] == "candidate-001"
    assert log["result_status"] == "APPROVED"
