from __future__ import annotations

from pathlib import Path
from typing import Any

from services.repair.repair_models import RepairCandidate, RepairCase, RepairDecision, to_plain_data
from services.taskflow.taskflow_artifacts import write_json_artifact


def _slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    return "-".join(part for part in cleaned.split("-") if part)[:80] or "repair"


def prepare_draft_pr(context: dict[str, Any]) -> dict[str, Any]:
    import json
    from datetime import datetime, UTC
    from pathlib import Path
    from services.repair.taskflow_artifacts import artifact_dir_for_run, write_step_artifact
    
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    output_root = context.get("output_root")
    
    run_dir = artifact_dir_for_run(incident_id, run_id, output_root)
    
    # ── 1. Load and validate Human Gate Decision ──
    gate_path = run_dir / "human_gate_decision.json"
    if not gate_path.exists():
        raise ValueError("Human Gate Decision artifact is missing.")
        
    gate_data = json.loads(gate_path.read_text(encoding="utf-8"))
    gate_status = gate_data.get("status")
    if gate_status not in {"APPROVED", "DRAFT_PR_ONLY"}:
        raise ValueError(
            f"Human Gate status '{gate_status}' blocks draft PR preparation. APPROVED or DRAFT_PR_ONLY is required."
        )
        
    selected_candidate_id = gate_data.get("selected_candidate_id")
    if not selected_candidate_id:
        raise ValueError("No candidate selected in Human Gate Decision.")
        
    # ── 1b. Load and validate Patch Tournament Result ──
    tournament_path = run_dir / "tournament_result.json"
    if tournament_path.exists():
        tournament_data = json.loads(tournament_path.read_text(encoding="utf-8"))
        tournament_selected = tournament_data.get("selected_candidate_id")
        
        # Human Gate selected candidate ile tournament selected candidate uyumlu olmalı
        if tournament_selected != selected_candidate_id:
            raise ValueError(
                f"Cannot prepare draft PR: Human Gate selected candidate '{selected_candidate_id}' "
                f"does not match tournament selected candidate '{tournament_selected}'."
            )
            
        # Tournament selected candidate disqualified ise Draft PR bloklanmalı
        found_candidate = None
        for cand in tournament_data.get("candidates") or []:
            if cand.get("candidate_id") == selected_candidate_id:
                found_candidate = cand
                break
        if found_candidate and not found_candidate.get("eligible", False):
            raise ValueError(
                f"Cannot prepare draft PR: Selected candidate '{selected_candidate_id}' "
                f"is disqualified in the tournament."
            )
        
    # ── 2. Load and validate PR Review ──
    review_path = run_dir / "pr_review.json"
    if not review_path.exists():
        raise ValueError("PR review artifact (pr_review.json) is missing.")
        
    review_data = json.loads(review_path.read_text(encoding="utf-8"))
    if review_data.get("status") != "completed":
        raise ValueError(f"PR review status '{review_data.get('status')}' is not completed.")
        
    blocking_comments = review_data.get("blocking_comments") or []
    if blocking_comments:
        ack = context.get("operator_acknowledged_blocking_comments") or gate_data.get("operator_acknowledged_blocking_comments")
        if not ack:
            raise ValueError(
                f"Cannot prepare draft PR: Active blocking comments exist in PR review, "
                f"but operator has not acknowledged them. Comments: {blocking_comments}"
            )
            
    # ── 3. Load and validate Patch Candidates ──
    candidates_path = run_dir / "patch_candidates.json"
    if not candidates_path.exists():
        # Fallback to incident root
        fallback_root = Path(output_root) if output_root else Path("repair_outputs")
        candidates_path = fallback_root / incident_id / "patch_candidates.json"
        
    if not candidates_path.exists():
        raise ValueError("Patch candidates artifact is missing.")
        
    candidates_data = json.loads(candidates_path.read_text(encoding="utf-8"))
    candidate_item = None
    if isinstance(candidates_data, list):
        for c in candidates_data:
            if c.get("candidate_id") == selected_candidate_id:
                candidate_item = c
                break
    elif isinstance(candidates_data, dict):
        if "candidates" in candidates_data:
            for c in candidates_data["candidates"]:
                if c.get("candidate_id") == selected_candidate_id:
                    candidate_item = c
                    break
        elif candidates_data.get("candidate_id") == selected_candidate_id:
            candidate_item = candidates_data
            
    if not candidate_item:
        raise ValueError(f"Selected candidate ID '{selected_candidate_id}' is not in patch candidates list.")
        
    # ── 4. Load and validate Sandbox Result ──
    sandbox_path = run_dir / "sandbox_result.json"
    if not sandbox_path.exists():
        fallback_root = Path(output_root) if output_root else Path("repair_outputs")
        sandbox_path = fallback_root / incident_id / "sandbox_result.json"
        
    if not sandbox_path.exists():
        raise ValueError("Sandbox result artifact is missing.")
        
    sandbox_data = json.loads(sandbox_path.read_text(encoding="utf-8"))
    tests_passed = False
    if isinstance(sandbox_data, dict):
        if selected_candidate_id in sandbox_data:
            tests_passed = sandbox_data[selected_candidate_id].get("tests_passed", False) or sandbox_data[selected_candidate_id].get("status") == "passed"
        else:
            tests_passed = sandbox_data.get("tests_passed", False) or sandbox_data.get("status") == "passed"
            
    if not tests_passed:
        raise ValueError(f"Cannot prepare draft PR: Sandbox tests did not pass.")
        
    # ── 5. Load and validate Verifier Mesh Result ──
    verifier_path = run_dir / "verifier_mesh_result.json"
    if not verifier_path.exists():
        fallback_root = Path(output_root) if output_root else Path("repair_outputs")
        verifier_path = fallback_root / incident_id / "verifier_mesh_result.json"
        
    if not verifier_path.exists():
        raise ValueError("Verifier mesh result artifact is missing.")
        
    verifier_data = json.loads(verifier_path.read_text(encoding="utf-8"))
    v_status = verifier_data.get("status")
    # Accept if verifier passed, is warning, is VERIFIER_PASSED, or if status is not explicitly failed
    if v_status in {"failed", "VERIFIER_FAILED"}:
        raise ValueError(f"Cannot prepare draft PR: Verifier mesh status is '{v_status}'.")
        
    # ── 6. Build draft_pr_metadata.json ──
    risk_score = float(gate_data.get("risk_score") or 0.0)
    risk_level = gate_data.get("risk_level") or "MEDIUM"
    
    # Get relative paths for artifact refs
    rel_prefix = f"{incident_id}/taskflow/{run_id}"
    
    artifact_refs = {
        "repair_case": f"{rel_prefix}/repair_case.json",
        "patch_candidates": f"{rel_prefix}/patch_candidates.json" if (run_dir / "patch_candidates.json").exists() else f"{incident_id}/patch_candidates.json",
        "sandbox_result": f"{rel_prefix}/sandbox_result.json" if (run_dir / "sandbox_result.json").exists() else f"{incident_id}/sandbox_result.json",
        "verifier_mesh_result": f"{rel_prefix}/verifier_mesh_result.json" if (run_dir / "verifier_mesh_result.json").exists() else f"{incident_id}/verifier_mesh_result.json",
        "risk_report": f"{rel_prefix}/risk_report.json" if (run_dir / "risk_report.json").exists() else f"{incident_id}/risk_report.json",
        "human_gate_decision": f"{rel_prefix}/human_gate_decision.json",
        "pr_review": f"{rel_prefix}/pr_review.json"
    }
    
    changed_files = candidate_item.get("changed_files") or []
    branch_name = f"repair/{incident_id}"
    
    payload = {
        "status": "DRAFT_PR_READY",
        "incident_id": incident_id,
        "run_id": run_id,
        "title": f"fix: repair {incident_id}",
        "body": "\n".join([
            "## Summary",
            f"Automated repair draft PR for incident {incident_id}.",
            "",
            "## Human Gate decision",
            f"- Status: {gate_status}",
            f"- Selected Candidate: {selected_candidate_id}",
            f"- Rationale: {gate_data.get('rationale')}",
            "",
            "## Risk Decision",
            f"- Risk Score: {risk_score}",
            f"- Risk Level: {risk_level}",
            "",
            "## Changed files",
            *[f"- {path}" for path in changed_files]
        ]),
        "base_branch": "main",
        "head_branch": branch_name,
        "selected_candidate_id": selected_candidate_id,
        "human_gate_status": gate_status,
        "human_gate_decision": gate_data.get("decision") or "open_draft_pr_only",
        "risk_score": risk_score,
        "risk_level": risk_level,
        "changed_files": changed_files,
        "artifact_refs": artifact_refs,
        "created_at": datetime.now(UTC).isoformat()
    }
    
    # Write metadata artifact
    artifact_info = write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="prepare_draft_pr",
        artifact_name="draft_pr_metadata.json",
        payload=payload,
        output_root=output_root,
    )
    
    # Update taskflow_run.json status -> "PR_DRAFTED"
    taskflow_run_path = run_dir / "taskflow_run.json"
    if taskflow_run_path.exists():
        try:
            taskflow_run_data = json.loads(taskflow_run_path.read_text(encoding="utf-8"))
            taskflow_run_data["status"] = "PR_DRAFTED"
            taskflow_run_path.write_text(json.dumps(taskflow_run_data, indent=2, sort_keys=True), encoding="utf-8")
        except Exception:
            pass
            
    return {"draft_pr": payload, "artifact_path": artifact_info["path"], "artifact_type": "json"}

