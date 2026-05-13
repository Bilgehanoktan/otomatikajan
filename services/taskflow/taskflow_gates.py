from __future__ import annotations

from typing import Any

from services.taskflow.taskflow_models import GateDecision


def decision_for_risk(risk_score: float) -> str:
    if risk_score <= 0.30:
        return "DRAFT_PR_ALLOWED"
    if risk_score <= 0.60:
        return "HUMAN_APPROVAL_REQUIRED"
    if risk_score <= 0.80:
        return "QUORUM_REQUIRED"
    return "AUTO_REPAIR_BLOCKED"


def evaluate_gate(context: dict[str, Any]) -> dict[str, Any]:
    risk_score = float(context.get("risk_score") or 0.0)
    decision = decision_for_risk(risk_score)
    gate = GateDecision(
        gate_id="approval_gate",
        decision=decision,
        risk_score=round(risk_score, 2),
        reason=f"Risk score {risk_score:.2f} için gate kararı üretildi.",
        required_approval=None if decision == "DRAFT_PR_ALLOWED" else decision,
    )
    return {
        "gate_decision": gate,
        "final_decision": decision,
        "workflow_status": "WAITING_HUMAN" if decision in {"HUMAN_APPROVAL_REQUIRED", "QUORUM_REQUIRED"} else (
            "BLOCKED" if decision == "AUTO_REPAIR_BLOCKED" else "DRAFT_PR_READY"
        ),
    }

