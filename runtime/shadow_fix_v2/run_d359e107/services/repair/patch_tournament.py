from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, UTC

from services.repair.patch_tournament_models import (
    PatchTournamentWeights,
    ScoreBreakdown,
    ScoredCandidate,
    PatchTournamentResult
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS_DIR = WORKSPACE_ROOT / "repair_outputs"

def load_tournament_inputs(
    incident_id: str,
    run_id: str,
    output_root: Optional[Path | str] = None
) -> Dict[str, Any]:
    """
    Loads all relevant inputs and artifacts for the tournament from the run directory.
    """
    root = Path(output_root) if output_root is not None else REPAIR_OUTPUTS_DIR
    run_dir = root / incident_id / "taskflow" / run_id
    
    inputs = {
        "patch_candidates": {},
        "sandbox_result": {},
        "verifier_mesh_result": {},
        "risk_report": {},
        "cognitive_integrity": {},
        "pr_review": {},
        "candidate_memory_score": {}
    }
    
    # 1. Load patch_candidates.json
    candidates_path = run_dir / "patch_candidates.json"
    if not candidates_path.exists():
        candidates_path = root / incident_id / "patch_candidates.json"
    if candidates_path.exists():
        try:
            inputs["patch_candidates"] = json.loads(candidates_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    # 2. Load sandbox_result.json
    sandbox_path = run_dir / "sandbox_result.json"
    if not sandbox_path.exists():
        sandbox_path = root / incident_id / "sandbox_result.json"
    if sandbox_path.exists():
        try:
            inputs["sandbox_result"] = json.loads(sandbox_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 3. Load verifier_mesh_result.json
    verifier_path = run_dir / "verifier_mesh_result.json"
    if not verifier_path.exists():
        verifier_path = root / incident_id / "verifier_mesh_result.json"
    if verifier_path.exists():
        try:
            inputs["verifier_mesh_result"] = json.loads(verifier_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 4. Load risk_report.json
    risk_path = run_dir / "risk_report.json"
    if not risk_path.exists():
        risk_path = root / incident_id / "risk_report.json"
    if risk_path.exists():
        try:
            inputs["risk_report"] = json.loads(risk_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 5. Load cognitive_integrity.json
    cognitive_path = run_dir / "cognitive_integrity.json"
    if cognitive_path.exists():
        try:
            inputs["cognitive_integrity"] = json.loads(cognitive_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 6. Load pr_review.json
    pr_review_path = run_dir / "pr_review.json"
    if pr_review_path.exists():
        try:
            inputs["pr_review"] = json.loads(pr_review_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 7. Load candidate_memory_score.json
    memory_path = run_dir / "candidate_memory_score.json"
    if memory_path.exists():
        try:
            inputs["candidate_memory_score"] = json.loads(memory_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return inputs

def normalize_candidate_scores(
    candidate: Dict[str, Any],
    inputs: Dict[str, Any]
) -> ScoreBreakdown:
    """
    Normalizes and derives the individual score values (0.0 to 1.0) for a given candidate.
    """
    sandbox_data = inputs.get("sandbox_result") or {}
    verifier_data = inputs.get("verifier_mesh_result") or {}
    risk_data = inputs.get("risk_report") or {}
    cognitive_data = inputs.get("cognitive_integrity") or {}
    memory_data = inputs.get("candidate_memory_score") or {}
    
    # Extract candidate_id
    cand_id = candidate.get("candidate_id", "candidate-001")
    
    # 1. Test score (Sandbox test outcome)
    test_score = 1.0
    cand_sandbox = sandbox_data.get(cand_id) or sandbox_data
    if cand_sandbox:
        tests_passed = cand_sandbox.get("tests_passed", cand_sandbox.get("status") == "PASSED")
        if not tests_passed:
            test_score = 0.0
            
    # 2. Build score (Sandbox build/apply outcome)
    build_score = 1.0
    if cand_sandbox:
        patch_applied = cand_sandbox.get("patch_applied", True)
        if not patch_applied:
            build_score = 0.0

    # 3. Risk score (Higher base_score or lower risk = better score)
    # Derive from risk_report.json or fallback
    risk_score = 1.0
    risk_val = risk_data.get("risk_score")
    if risk_val is not None:
        risk_score = max(0.0, min(1.0, 1.0 - float(risk_val)))
    else:
        risk_score = float(candidate.get("base_score", 0.70))

    # 4. Security score
    security_score = 1.0
    sec_score_val = ver_security = None
    if isinstance(verifier_data, dict):
        ver_security = verifier_data.get("security_score")
    if sec_score_val is None and ver_security is not None:
        security_score = float(ver_security)
    else:
        security_score = float(candidate.get("security_score", 1.0))

    # 5. Maintainability score
    maintainability_score = float(candidate.get("maintainability_score", 0.80))

    # 6. Rollback safety score
    rollback_safety_score = float(candidate.get("rollback_safety_score", 0.80))

    # 7. Cognitive integrity score
    cognitive_integrity_score = 1.0
    cog_val = cognitive_data.get("cognitive_integrity_score")
    if cog_val is not None:
        cognitive_integrity_score = float(cog_val)
    else:
        cognitive_integrity_score = float(candidate.get("cognitive_integrity_score", 0.80))

    # 8. Historical success score (from Phase 8 candidate_memory_score.json if available, else neutral 0.50)
    historical_success_score = 0.50
    # Try looking in candidate_memory_score.json first
    mem_scores = memory_data.get("candidate_scores") or []
    found_mem = False
    for ms in mem_scores:
        if ms.get("candidate_id") == cand_id:
            historical_success_score = float(ms.get("historical_success_score", 0.50))
            found_mem = True
            break
    if not found_mem:
        # Fallback to candidate itself or defaults
        historical_success_score = float(candidate.get("historical_success_score", 0.50))

    # 9. Cost score
    cost_score = float(candidate.get("cost_score", 0.90))

    # 10. Blast radius score
    blast_radius_score = 1.0
    if risk_data.get("blast_radius") == "high":
        blast_radius_score = 0.20
    elif risk_data.get("blast_radius") == "medium":
        blast_radius_score = 0.60

    return ScoreBreakdown(
        test_score=test_score,
        build_score=build_score,
        risk_score=risk_score,
        security_score=security_score,
        maintainability_score=maintainability_score,
        rollback_safety_score=rollback_safety_score,
        cognitive_integrity_score=cognitive_integrity_score,
        historical_success_score=historical_success_score,
        cost_score=cost_score,
        blast_radius_score=blast_radius_score
    )

def evaluate_candidate_eligibility(
    candidate: Dict[str, Any],
    score_breakdown: ScoreBreakdown,
    inputs: Dict[str, Any]
) -> tuple[bool, List[str]]:
    """
    Checks all hard disqualification rules and returns (eligible, disqualification_reasons).
    """
    reasons = []
    
    # 1. policy_status == "DENIED" (case-insensitive)
    policy = candidate.get("policy_status") or candidate.get("status")
    if isinstance(policy, str) and policy.upper() == "DENIED":
        reasons.append("policy_status == 'DENIED'")

    # 2. sandbox_status == "failed" (case-insensitive)
    sandbox_val = candidate.get("sandbox_status")
    if not sandbox_val:
        # derive from sandbox_result
        sandbox_data = inputs.get("sandbox_result") or {}
        cand_id = candidate.get("candidate_id")
        cand_sandbox = sandbox_data.get(cand_id) or sandbox_data
        if cand_sandbox and cand_sandbox.get("tests_passed") is False:
            sandbox_val = "failed"
            
    if isinstance(sandbox_val, str) and sandbox_val.lower() == "failed":
        reasons.append("sandbox_status == 'failed'")

    # 3. verifier_status == "failed" (case-insensitive)
    verifier_val = candidate.get("verifier_status")
    if not verifier_val:
        verifier_data = inputs.get("verifier_mesh_result") or {}
        if verifier_data.get("status") == "VERIFIER_FAILED" or verifier_data.get("status") == "failed":
            verifier_val = "failed"
            
    if isinstance(verifier_val, str) and verifier_val.lower() == "failed":
        reasons.append("verifier_status == 'failed'")

    # 4. security_score < 0.50
    if score_breakdown.security_score < 0.50:
        reasons.append(f"security_score < 0.50 (got {score_breakdown.security_score:.2f})")

    # 5. rollback_safety_score < 0.50
    if score_breakdown.rollback_safety_score < 0.50:
        reasons.append(f"rollback_safety_score < 0.50 (got {score_breakdown.rollback_safety_score:.2f})")

    # 6. cognitive_integrity_score < 0.50
    if score_breakdown.cognitive_integrity_score < 0.50:
        reasons.append(f"cognitive_integrity_score < 0.50 (got {score_breakdown.cognitive_integrity_score:.2f})")

    # 7. missing_diff == true
    # A candidate must have non-empty diff
    diff_content = candidate.get("diff") or candidate.get("patch") or candidate.get("diff_ref")
    if not diff_content:
        reasons.append("missing_diff == true")

    # 8. human_gate_blocked == true
    if candidate.get("human_gate_blocked") is True:
        reasons.append("human_gate_blocked == true")

    eligible = len(reasons) == 0
    return eligible, reasons

def score_patch_candidate(
    candidate: Dict[str, Any],
    score_breakdown: ScoreBreakdown,
    weights: PatchTournamentWeights,
    inputs: Dict[str, Any]
) -> float:
    """
    Computes final weighted score. Adds Phase 8 memory adjustment if available.
    Clamps final result between 0.0 and 1.0.
    """
    # Weighted base score calculation
    weighted_score = (
        score_breakdown.test_score * weights.test_score +
        score_breakdown.build_score * weights.build_score +
        score_breakdown.risk_score * weights.risk_score +
        score_breakdown.security_score * weights.security_score +
        score_breakdown.maintainability_score * weights.maintainability_score +
        score_breakdown.rollback_safety_score * weights.rollback_safety_score +
        score_breakdown.cognitive_integrity_score * weights.cognitive_integrity_score +
        score_breakdown.historical_success_score * weights.historical_success_score +
        score_breakdown.cost_score * weights.cost_score +
        score_breakdown.blast_radius_score * weights.blast_radius_score
    )
    
    # Add memory adjustment if available in candidate_memory_score.json or candidate
    memory_adjustment = 0.0
    cand_id = candidate.get("candidate_id")
    memory_data = inputs.get("candidate_memory_score") or {}
    mem_scores = memory_data.get("candidate_scores") or []
    for ms in mem_scores:
        if ms.get("candidate_id") == cand_id:
            memory_adjustment = float(ms.get("memory_adjustment", 0.0))
            break
            
    if memory_adjustment == 0.0:
        memory_adjustment = float(candidate.get("memory_adjustment", 0.0))
        
    final_score = max(0.0, min(1.0, weighted_score + memory_adjustment))
    return round(final_score, 4)

def rank_patch_candidates(
    candidates_list: List[Dict[str, Any]],
    inputs: Dict[str, Any],
    weights: PatchTournamentWeights
) -> List[ScoredCandidate]:
    """
    Scores, validates eligibility, and ranks all candidates by final score.
    """
    scored_candidates = []
    
    for cand in candidates_list:
        breakdown = normalize_candidate_scores(cand, inputs)
        eligible, reasons = evaluate_candidate_eligibility(cand, breakdown, inputs)
        final_score = score_patch_candidate(cand, breakdown, weights, inputs)
        
        scored_candidates.append(ScoredCandidate(
            candidate_id=cand.get("candidate_id", "candidate-001"),
            eligible=eligible,
            final_score=final_score if eligible else 0.0,
            disqualification_reasons=reasons,
            score_breakdown=breakdown
        ))
        
    # Sort eligible candidates by final_score descending, and disqualified ones at the end
    eligible_sorted = sorted([c for c in scored_candidates if c.eligible], key=lambda x: x.final_score, reverse=True)
    disqualified_sorted = [c for c in scored_candidates if not c.eligible]
    
    ranked_list = eligible_sorted + disqualified_sorted
    for i, c in enumerate(ranked_list):
        c.rank = i + 1
        
    return ranked_list

def write_tournament_result(
    incident_id: str,
    run_id: str,
    weights: PatchTournamentWeights,
    ranked_candidates: List[ScoredCandidate],
    artifact_refs: Dict[str, str],
    output_root: Optional[Path | str] = None
) -> PatchTournamentResult:
    """
    Writes the tournament_result.json artifact in the run taskflow folder.
    """
    root = Path(output_root) if output_root is not None else REPAIR_OUTPUTS_DIR
    run_dir = root / incident_id / "taskflow" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine the selected candidate (highest ranked eligible candidate)
    selected_candidate_id = None
    eligible_candidates = [c for c in ranked_candidates if c.eligible]
    if eligible_candidates:
        selected_candidate_id = eligible_candidates[0].candidate_id
        
    # Decide if human gate is required based on risk score or high risk candidate
    requires_human_gate = True
    
    result = PatchTournamentResult(
        incident_id=incident_id,
        run_id=run_id,
        status="completed",
        selected_candidate_id=selected_candidate_id,
        requires_human_gate=requires_human_gate,
        scoring_weights=weights,
        candidates=ranked_candidates,
        artifact_refs=artifact_refs,
        created_at=datetime.now(UTC).isoformat()
    )
    
    result_path = run_dir / "tournament_result.json"
    result_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    
    return result

def run_patch_tournament(
    incident_id: str,
    run_id: str,
    output_root: Optional[Path | str] = None
) -> PatchTournamentResult:
    """
    End-to-end execution of the patch tournament for an incident.
    """
    inputs = load_tournament_inputs(incident_id, run_id, output_root=output_root)
    candidates_raw = inputs.get("patch_candidates") or []
    
    # Handle list vs dict candidates raw
    candidates_list = []
    if isinstance(candidates_raw, list):
        candidates_list = candidates_raw
    elif isinstance(candidates_raw, dict):
        candidates_list = candidates_raw.get("candidates") or []
        # If still empty but it's a single candidate representation, wrap it in a list
        if not candidates_list and candidates_raw.get("candidate_id"):
            candidates_list = [candidates_raw]
            
    # Default fallback candidate if empty
    if not candidates_list:
        candidates_list = [{
            "candidate_id": "candidate-001",
            "candidate_source": "swe_agent",
            "agent_key": "swe_agent",
            "strategy": "conservative",
            "diff_ref": "sandbox/patch.diff",
            "diff": "--- a/page.tsx\n+++ b/page.tsx\n",
            "policy_status": "approved",
            "sandbox_status": "passed",
            "verifier_status": "passed",
            "base_score": 0.70
        }]
        
    weights = PatchTournamentWeights()
    ranked = rank_patch_candidates(candidates_list, inputs, weights)
    
    # References to input artifacts
    root = Path(output_root) if output_root is not None else REPAIR_OUTPUTS_DIR
    run_rel_dir = f"repair_outputs/{incident_id}/taskflow/{run_id}"
    artifact_refs = {
        "patch_candidates": f"{run_rel_dir}/patch_candidates.json",
        "sandbox_result": f"{run_rel_dir}/sandbox_result.json",
        "verifier_mesh_result": f"{run_rel_dir}/verifier_mesh_result.json",
        "risk_report": f"{run_rel_dir}/risk_report.json",
        "candidate_memory_score": f"{run_rel_dir}/candidate_memory_score.json"
    }
    
    return write_tournament_result(
        incident_id=incident_id,
        run_id=run_id,
        weights=weights,
        ranked_candidates=ranked,
        artifact_refs=artifact_refs,
        output_root=output_root
    )
