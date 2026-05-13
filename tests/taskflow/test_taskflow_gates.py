from services.taskflow.taskflow_gates import decision_for_risk, evaluate_gate


def test_gate_thresholds():
    assert decision_for_risk(0.30) == "DRAFT_PR_ALLOWED"
    assert decision_for_risk(0.31) == "HUMAN_APPROVAL_REQUIRED"
    assert decision_for_risk(0.61) == "QUORUM_REQUIRED"
    assert decision_for_risk(0.81) == "AUTO_REPAIR_BLOCKED"


def test_evaluate_gate_returns_waiting_human_for_medium_risk():
    result = evaluate_gate({"risk_score": 0.5})

    assert result["gate_decision"].decision == "HUMAN_APPROVAL_REQUIRED"
    assert result["workflow_status"] == "WAITING_HUMAN"

