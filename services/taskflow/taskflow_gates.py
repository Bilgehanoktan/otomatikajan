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
    from services.repair.taskflow_artifacts import read_step_artifact, write_step_artifact
    
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    output_root = context.get("output_root")
    
    risk_score = float(context.get("risk_score") or 0.0)
    decision = decision_for_risk(risk_score)
    
    # ── Phase 9: Read tournament_result.json ─────────────────────────────────
    selected_candidate_id = None
    requires_human_gate = True
    eligible_candidate_found = False
    
    try:
        tournament_data = read_step_artifact(incident_id, run_id, "tournament_result.json", output_root)
        selected_candidate_id = tournament_data.get("selected_candidate_id")
        requires_human_gate = tournament_data.get("requires_human_gate", True)
        
        # Check if selected_candidate_id is eligible
        if selected_candidate_id:
            for cand in tournament_data.get("candidates") or []:
                if cand.get("candidate_id") == selected_candidate_id:
                    eligible_candidate_found = cand.get("eligible", False)
                    break
    except Exception:
        # Fallback to candidate in context
        candidate = context.get("repair_candidate")
        if candidate:
            if isinstance(candidate, dict):
                selected_candidate_id = candidate.get("candidate_id") or "candidate-01"
            elif hasattr(candidate, "candidate_id"):
                selected_candidate_id = candidate.candidate_id
        eligible_candidate_found = True  # Fallback to True
        requires_human_gate = risk_score > 0.30

    # If requires_human_gate is True, we cannot bypass (cannot be DRAFT_PR_ALLOWED)
    if requires_human_gate and decision == "DRAFT_PR_ALLOWED":
        decision = "HUMAN_APPROVAL_REQUIRED"
        
    # Hard disqualification check: if no eligible candidate found, block the gate!
    if not eligible_candidate_found or selected_candidate_id is None:
        decision = "AUTO_REPAIR_BLOCKED"
        
    gate = GateDecision(
        gate_id="approval_gate",
        decision=decision,
        risk_score=round(risk_score, 2),
        reason=f"Risk score {risk_score:.2f} ve tournament girdileri ile gate kararı üretildi.",
        required_approval=None if decision == "DRAFT_PR_ALLOWED" else decision,
    )
    
    candidate_ids = [selected_candidate_id] if selected_candidate_id else []
    
    waiting_reason = ""
    if decision == "AUTO_REPAIR_BLOCKED":
        waiting_reason = "No eligible patch candidates found or selected candidate is disqualified."
    elif decision != "DRAFT_PR_ALLOWED":
        waiting_reason = f"Risk score {risk_score:.2f} or tournament requires operator review."
    else:
        waiting_reason = "Risk score is within safe limits. Human approval bypassed."

    gate_payload = {
        "status": "APPROVED" if decision == "DRAFT_PR_ALLOWED" else (
            "BLOCKED" if decision == "AUTO_REPAIR_BLOCKED" else "WAITING_FOR_OPERATOR"
        ),
        "incident_id": incident_id,
        "run_id": run_id,
        "operator_required": decision != "DRAFT_PR_ALLOWED" and decision != "AUTO_REPAIR_BLOCKED",
        "risk_score": round(risk_score, 2),
        "risk_threshold": 0.30,
        "waiting_reason": waiting_reason,
        "candidate_ids": candidate_ids,
        "required_decision_fields": [
            "operator_id",
            "decision",
            "rationale",
            "selected_candidate_id",
            "risk_acknowledgement",
            "rollback_required"
        ],
        "artifact_refs": {
            "risk_report": f"repair_outputs/{incident_id}/taskflow/{run_id}/risk_report.json",
            "patch_candidates": f"repair_outputs/{incident_id}/taskflow/{run_id}/patch_candidates.json",
            "verifier_mesh_result": f"repair_outputs/{incident_id}/taskflow/{run_id}/verifier_mesh_result.json",
            "sandbox_result": f"repair_outputs/{incident_id}/taskflow/{run_id}/sandbox_result.json",
            "tournament_result": f"repair_outputs/{incident_id}/taskflow/{run_id}/tournament_result.json"
        }
    }
    
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="approval_gate",
        artifact_name="human_gate_decision.json",
        payload=gate_payload,
        output_root=context.get("output_root")
    )

    return {
        "gate_decision": gate,
        "final_decision": decision,
        "workflow_status": "WAITING_HUMAN" if decision in {"HUMAN_APPROVAL_REQUIRED", "QUORUM_REQUIRED"} else (
            "BLOCKED" if decision == "AUTO_REPAIR_BLOCKED" else "DRAFT_PR_READY"
        ),
    }

