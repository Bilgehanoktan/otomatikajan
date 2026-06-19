from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

# Default path setups
def get_outcomes_path(output_root: str | Path | None = None) -> Path:
    root = Path(output_root) if output_root is not None else Path.cwd() / "repair_outputs"
    path = root / "learning_memory" / "outcomes.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_profile_path(agent_key: str, strategy: str, output_root: str | Path | None = None) -> Path:
    root = Path(output_root) if output_root is not None else Path.cwd() / "repair_outputs"
    path = root / "learning_memory" / "profiles" / f"{agent_key}_{strategy}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def record_repair_outcome(
    incident_id: str,
    run_id: str,
    finding_id: str,
    selected_candidate_id: str,
    candidate_source: str,
    agent_key: str,
    strategy: str,
    decision: str,
    human_gate_status: str,
    risk_score: float,
    risk_prediction_accuracy: float | None,
    test_result: str,
    post_decision_result: str,
    operator_rationale: str,
    created_at: str | None = None,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    """Records the outcome of a repair attempt to outcomes.jsonl and updates the success profile."""
    if created_at is None:
        created_at = datetime.now(UTC).isoformat()
        
    outcome = {
        "incident_id": incident_id,
        "run_id": run_id,
        "finding_id": finding_id,
        "selected_candidate_id": selected_candidate_id,
        "candidate_source": candidate_source,
        "agent_key": agent_key,
        "strategy": strategy,
        "decision": decision,
        "human_gate_status": human_gate_status,
        "risk_score": risk_score,
        "risk_prediction_accuracy": risk_prediction_accuracy,
        "test_result": test_result,
        "post_decision_result": post_decision_result,
        "operator_rationale": operator_rationale,
        "created_at": created_at,
    }
    
    # Append to outcomes.jsonl
    outcomes_file = get_outcomes_path(output_root)
    with outcomes_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(outcome, sort_keys=True) + "\n")
        
    # Update the strategy success profile
    update_strategy_success_profile(agent_key, strategy, outcome, output_root)
    
    # Save the learning_memory_update.json artifact in the taskflow run directory
    from services.repair.taskflow_artifacts import write_step_artifact
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="update_learning_memory",
        artifact_name="learning_memory_update.json",
        payload=outcome,
        output_root=output_root,
    )
    
    return outcome


def load_strategy_success_profile(
    agent_key: str,
    strategy: str,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    """Loads a strategy's success profile from disk, creating a new one if it doesn't exist."""
    profile_file = get_profile_path(agent_key, strategy, output_root)
    if profile_file.exists():
        try:
            return json.loads(profile_file.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    # Default strategy profile
    return {
        "agent_key": agent_key,
        "strategy": strategy,
        "total_attempts": 0,
        "successful_attempts": 0,
        "failed_attempts": 0,
        "human_approved_count": 0,
        "draft_pr_ready_count": 0,
        "average_risk_score": 0.0,
        "last_success_at": None,
        "last_result": None,
        "historical_success_score": 0.0,
    }


def update_strategy_success_profile(
    agent_key: str,
    strategy: str,
    outcome: dict[str, Any],
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    """Updates a strategy success profile with the new outcome and saves it to disk."""
    profile = load_strategy_success_profile(agent_key, strategy, output_root)
    
    # Calculate counts and metrics
    profile["total_attempts"] += 1
    
    is_success = outcome.get("test_result") == "passed" and outcome.get("human_gate_status") in {"APPROVED", "DRAFT_PR_ONLY", "approve_and_apply", "approve_and_merge"}
    
    if is_success:
        profile["successful_attempts"] += 1
        profile["last_success_at"] = outcome.get("created_at")
        profile["last_result"] = "success"
    else:
        profile["failed_attempts"] += 1
        profile["last_result"] = "failed"
        
    if outcome.get("human_gate_status") in {"APPROVED", "DRAFT_PR_ONLY", "approve_and_apply", "approve_and_merge"}:
        profile["human_approved_count"] += 1
        
    if outcome.get("post_decision_result") == "draft_pr_ready" or outcome.get("decision") == "open_draft_pr_only":
        profile["draft_pr_ready_count"] += 1
        
    # Recalculate average risk score
    prev_total = profile["total_attempts"] - 1
    prev_avg = profile.get("average_risk_score", 0.0)
    new_risk = outcome.get("risk_score", 0.0)
    profile["average_risk_score"] = round((prev_avg * prev_total + new_risk) / profile["total_attempts"], 2)
    
    # Recalculate success score
    profile["historical_success_score"] = round(profile["successful_attempts"] / profile["total_attempts"], 2)
    
    # Save profile to disk
    profile_file = get_profile_path(agent_key, strategy, output_root)
    profile_file.write_text(json.dumps(profile, indent=2, sort_keys=True), encoding="utf-8")
    
    # Also write step artifact if run context matches (useful for TaskFlow run artifacts list)
    from services.repair.taskflow_artifacts import write_step_artifact
    incident_id = outcome.get("incident_id") or "INC-UNKNOWN"
    run_id = outcome.get("run_id") or "RUN-UNKNOWN"
    try:
        write_step_artifact(
            incident_id=incident_id,
            run_id=run_id,
            step_id="update_learning_memory",
            artifact_name="strategy_success_profile.json",
            payload=profile,
            output_root=output_root,
        )
    except Exception:
        pass
        
    return profile


def score_candidates_with_memory(
    candidates: list[dict[str, Any]],
    incident_id: str,
    run_id: str,
    output_root: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Calculates memory-adjusted scores for all patch candidates based on historical performance profiles."""
    scored_candidates = []
    
    for cand in candidates:
        cand_id = cand.get("candidate_id") or cand.get("id")
        agent_key = cand.get("agent_key") or "mock_agent"
        strategy = cand.get("strategy") or "conservative"
        base_score = cand.get("base_score") or cand.get("confidence_score") or 0.50
        
        # Load performance profile
        profile = load_strategy_success_profile(agent_key, strategy, output_root)
        total = profile.get("total_attempts", 0)
        success_score = profile.get("historical_success_score", 0.0)
        
        adjustment = 0.0
        explanation = "No historical learning memory available"
        
        # Policy & Sandbox check
        is_policy_denied = cand.get("blocked_reason") is not None or cand.get("policy_denied") is True
        is_sandbox_failed = cand.get("sandbox_failed") is True or cand.get("test_score", 1.0) < 0.50
        
        if total >= 3:
            # Base success score contribution
            base_adj = (success_score - 0.5) * 0.12
            adjustment += base_adj
            
            # Human approval bonus
            if profile.get("human_approved_count", 0) > 0:
                adjustment += 0.03
                
            # Draft PR ready bonus
            if profile.get("draft_pr_ready_count", 0) > 0:
                adjustment += 0.02
                
            # Recent failure penalty
            if profile.get("last_result") == "failed":
                adjustment += -0.05
                
            # Clamp memory adjustment to safe range [-0.10, 0.10]
            adjustment = max(-0.10, min(0.10, adjustment))
            explanation = f"Historical success bonus applied for {agent_key}/{strategy}"
        else:
            explanation = f"Insufficient history (attempts: {total}/3) for memory adjustments"
            
        # Denied / failed candidates cannot get positive memory adjustments
        if is_policy_denied:
            adjustment = -0.10
            explanation = f"Policy denied: Security/policy failure penalty applied for {agent_key}/{strategy}"
        elif is_sandbox_failed:
            adjustment = min(0.0, adjustment)
            # Add sandbox/verification penalty if adjustment wasn't already negative
            if adjustment >= 0.0:
                adjustment = -0.05
            explanation = f"Sandbox failed: memory bonus restricted for {agent_key}/{strategy}"
            
        final_score = round(max(0.0, min(1.0, base_score + adjustment)), 2)
        adjustment = round(adjustment, 2)
        
        scored_candidates.append({
            "candidate_id": cand_id,
            "agent_key": agent_key,
            "strategy": strategy,
            "base_score": base_score,
            "historical_success_score": success_score,
            "memory_adjustment": adjustment,
            "final_score": final_score,
            "explanation": explanation,
        })
        
    # Write candidate memory score artifact
    write_candidate_memory_score(incident_id, run_id, scored_candidates, output_root)
    
    return scored_candidates


def write_candidate_memory_score(
    incident_id: str,
    run_id: str,
    candidate_scores: list[dict[str, Any]],
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    """Writes the candidate memory score artifact to the taskflow run directory."""
    from services.repair.taskflow_artifacts import write_step_artifact
    payload = {
        "incident_id": incident_id,
        "run_id": run_id,
        "candidate_scores": candidate_scores,
    }
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="score_risk",
        artifact_name="candidate_memory_score.json",
        payload=payload,
        output_root=output_root,
    )
    return payload
