from __future__ import annotations

import json
from datetime import datetime, UTC
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Constants
REPO_ROOT = Path(__file__).resolve().parents[2]
REPAIR_OUTPUTS_DIR = REPO_ROOT / "repair_outputs"

class HumanGateStatus(str, Enum):
    WAITING_FOR_OPERATOR = "WAITING_FOR_OPERATOR"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
    DRAFT_PR_ONLY = "DRAFT_PR_ONLY"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"

class HumanGateDecisionType(str, Enum):
    APPROVE_CONSERVATIVE_PATCH = "approve_conservative_patch"
    APPROVE_RADICAL_PATCH = "approve_radical_patch"
    REQUEST_NEW_CANDIDATE = "request_new_candidate"
    SEND_TO_MANUAL_REVIEW = "send_to_manual_review"
    REJECT = "reject"
    OPEN_DRAFT_PR_ONLY = "open_draft_pr_only"
    RUN_MORE_TESTS = "run_more_tests"

class HumanGateDecisionRequest(BaseModel):
    operator_id: str
    decision: HumanGateDecisionType
    rationale: str
    selected_candidate_id: str
    risk_acknowledgement: bool
    rollback_required: bool
    rollback_plan_ref: Optional[str] = None
    artifact_refs: Optional[Dict[str, str]] = None

def _get_run_dir(incident_id: str, run_id: str) -> Path:
    return REPAIR_OUTPUTS_DIR / incident_id / "taskflow" / run_id

def record_human_gate_decision(
    incident_id: str,
    run_id: str,
    req: HumanGateDecisionRequest,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Validates and records an operator's human gate decision.
    Updates human_gate_decision.json and appends to human_gate_audit.jsonl.
    """
    root = output_root if output_root is not None else REPAIR_OUTPUTS_DIR
    run_dir = root / incident_id / "taskflow" / run_id
    gate_path = run_dir / "human_gate_decision.json"
    audit_path = run_dir / "human_gate_audit.jsonl"
    
    if not gate_path.exists():
        raise FileNotFoundError(f"Human gate artifact not found: {gate_path}")
        
    gate_data = json.loads(gate_path.read_text(encoding="utf-8"))
    
    # ── 1. Rationale validation ──────────────────────────────────────────────
    if not req.rationale or not req.rationale.strip():
        raise ValueError("Operator rationale cannot be empty.")
        
    # ── 2. Candidate inclusion validation ──────────────────────────────────────
    candidate_ids = gate_data.get("candidate_ids") or []
    if req.selected_candidate_id not in candidate_ids:
        raise ValueError(
            f"Selected candidate ID '{req.selected_candidate_id}' is not in the allowed list: {candidate_ids}"
        )
        
    # ── 3. Risk validation ───────────────────────────────────────────────────
    risk_score = gate_data.get("risk_score") or 0.0
    risk_threshold = gate_data.get("risk_threshold") or 0.30
    if risk_score > risk_threshold and not req.risk_acknowledgement:
        raise ValueError(
            f"Risk score {risk_score} exceeds threshold {risk_threshold}. Risk acknowledgement is required."
        )
        
    # ── 4. Rollback validation ────────────────────────────────────────────────
    if req.rollback_required and not req.rollback_plan_ref:
        raise ValueError("Rollback plan reference is required when rollback is enabled.")
        
    # ── 5. Candidate status & Verifier validation ──────────────────────────────
    # Load patch_candidates.json
    candidates_path = run_dir / "patch_candidates.json"
    if not candidates_path.exists():
        # Fallback to incident root
        candidates_path = root / incident_id / "patch_candidates.json"
        
    if not candidates_path.exists():
        raise FileNotFoundError(f"Patch candidates artifact is missing for verification.")
        
    candidates_data = json.loads(candidates_path.read_text(encoding="utf-8"))
    # Find the specific candidate
    candidate_item = None
    # We might have a list or a dict inside patch_candidates.json
    if isinstance(candidates_data, list):
        for c in candidates_data:
            if c.get("candidate_id") == req.selected_candidate_id:
                candidate_item = c
                break
    elif isinstance(candidates_data, dict):
        # Could be { "candidates": [...] }
        for c in candidates_data.get("candidates") or []:
            if c.get("candidate_id") == req.selected_candidate_id:
                candidate_item = c
                break
                
    if not candidate_item:
        raise ValueError(f"Candidate details for '{req.selected_candidate_id}' not found in candidates list.")
        
    # Check policy
    if candidate_item.get("policy_status") == "denied" or candidate_item.get("status") == "denied":
        raise ValueError(f"Cannot approve candidate '{req.selected_candidate_id}' as its policy status is DENIED.")
        
    # Load sandbox_result.json to check validation
    sandbox_path = run_dir / "sandbox_result.json"
    if not sandbox_path.exists():
        sandbox_path = root / incident_id / "sandbox_result.json"
        
    if not sandbox_path.exists():
        raise FileNotFoundError("Sandbox result artifact is missing for verification.")
        
    sandbox_data = json.loads(sandbox_path.read_text(encoding="utf-8"))
    
    # Check if sandbox has tests_passed
    tests_passed = True
    if isinstance(sandbox_data, dict):
        # We might have a dictionary where key is candidate_id or a general result
        if req.selected_candidate_id in sandbox_data:
            candidate_sandbox = sandbox_data[req.selected_candidate_id]
            tests_passed = candidate_sandbox.get("tests_passed", True)
        else:
            tests_passed = sandbox_data.get("tests_passed", True)
            
    if not tests_passed:
        raise ValueError(f"Cannot approve candidate '{req.selected_candidate_id}' as sandbox tests failed.")
        
    # Check verifier mesh result
    verifier_path = run_dir / "verifier_mesh_result.json"
    if not verifier_path.exists():
        verifier_path = root / incident_id / "verifier_mesh_result.json"
        
    if not verifier_path.exists():
        raise FileNotFoundError("Verifier mesh result artifact is missing for verification.")
        
    # ── 6. Mapping final status ──────────────────────────────────────────────
    if req.decision in {
        HumanGateDecisionType.APPROVE_CONSERVATIVE_PATCH,
        HumanGateDecisionType.APPROVE_RADICAL_PATCH
    }:
        final_status = HumanGateStatus.APPROVED
    elif req.decision == HumanGateDecisionType.REJECT:
        final_status = HumanGateStatus.REJECTED
    elif req.decision == HumanGateDecisionType.REQUEST_NEW_CANDIDATE:
        final_status = HumanGateStatus.REQUEST_MORE_EVIDENCE
    elif req.decision == HumanGateDecisionType.OPEN_DRAFT_PR_ONLY:
        final_status = HumanGateStatus.DRAFT_PR_ONLY
    elif req.decision in {HumanGateDecisionType.RUN_MORE_TESTS, HumanGateDecisionType.SEND_TO_MANUAL_REVIEW}:
        final_status = HumanGateStatus.WAITING_FOR_OPERATOR
    else:
        final_status = HumanGateStatus.WAITING_FOR_OPERATOR
        
    # Update human_gate_decision.json
    gate_data["status"] = final_status.value
    gate_data["operator_id"] = req.operator_id
    gate_data["decision"] = req.decision.value
    gate_data["rationale"] = req.rationale
    gate_data["selected_candidate_id"] = req.selected_candidate_id
    gate_data["risk_acknowledgement"] = req.risk_acknowledgement
    gate_data["rollback_required"] = req.rollback_required
    if req.rollback_plan_ref:
        gate_data["rollback_plan_ref"] = req.rollback_plan_ref
    gate_data["decided_at"] = datetime.now(UTC).isoformat()
    
    gate_path.write_text(json.dumps(gate_data, indent=2, sort_keys=True), encoding="utf-8")
    
    # Write to human_gate_audit.jsonl
    audit_entry = {
        "event": "human_gate_decision_recorded",
        "incident_id": incident_id,
        "run_id": run_id,
        "operator_id": req.operator_id,
        "decision": req.decision.value,
        "selected_candidate_id": req.selected_candidate_id,
        "rationale": req.rationale,
        "decided_at": gate_data["decided_at"],
        "result_status": final_status.value
    }
    
    # Append line to jsonl
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry) + "\n")
        
    return gate_data
