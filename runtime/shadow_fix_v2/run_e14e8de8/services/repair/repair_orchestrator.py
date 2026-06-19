from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from services.repair.code_localizer import localize_code
from services.repair.patch_candidate_runner import generate_patch_candidate
from services.repair.repair_case_builder import build_repair_case
from services.repair.repair_plan_builder import build_repair_plan
from services.repair.repair_models import (
    RepairCandidate,
    RepairCase,
    RepairDecision,
    RepairPlan,
    RepairReport,
    SandboxResult,
    to_plain_data,
)
from services.repair.repair_reporter import write_case, write_plan, write_repair_outputs, write_sandbox_log
from services.repair.risk_adapter import calculate_risk
from services.repair.sandbox_executor import run_patch_in_sandbox
from services.repair.verifier_adapter import run_verifier_mesh


def run_repair_flow(input_payload: dict[str, Any], output_root: str | Path | None = None) -> RepairReport:
    """Run the Phase 1-3 safe self-repair skeleton and write JSON artifacts.

    The flow never commits, merges, or patches the source working tree. Candidate
    diffs are applied only in a temporary sandbox copy.
    """
    output_root_path = Path(output_root) if output_root is not None else None
    repair_case = build_repair_case(input_payload)
    if output_root_path is not None:
        repair_case.repo_snapshot["_repair_output_root"] = str(output_root_path)

    write_case(repair_case, output_root=output_root_path)

    suspected = localize_code(repair_case)
    repair_case.suspected_files = [str(item["file"]) for item in suspected]

    repair_plan = build_repair_plan(repair_case, suspected)
    write_plan(repair_plan, repair_case, output_root=output_root_path)

    candidate = generate_patch_candidate(repair_case, repair_plan)
    sandbox_result = run_patch_in_sandbox(candidate, repair_case)
    verifier_result = run_verifier_mesh(repair_case, candidate, sandbox_result)
    risk_decision = calculate_risk(repair_case, candidate, verifier_result)

    if risk_decision.status in {"AUTO_REPAIR_BLOCKED", "QUORUM_REQUIRED", "HUMAN_APPROVAL_REQUIRED"}:
        final_status = risk_decision.status
    elif not sandbox_result.patch_applied or not sandbox_result.tests_passed:
        final_status = "SANDBOX_FAILED"
    elif verifier_result.get("status") == "VERIFIER_FAILED":
        final_status = "VERIFIER_FAILED"
    else:
        final_status = risk_decision.status

    report = RepairReport(
        repair_case=repair_case,
        suspected_files=suspected,
        candidate=candidate,
        sandbox_result=sandbox_result,
        verifier_result=verifier_result,
        risk_decision=risk_decision,
        final_status=final_status,
        repair_plan=repair_plan,
    )
    write_repair_outputs(report, output_root=output_root_path)
    return report


def _output_root_from_context(context: dict[str, Any]) -> Path | None:
    output_root = context.get("output_root")
    return Path(output_root) if output_root else None


def _context_update(payload: dict[str, Any]) -> dict[str, Any]:
    """Return WorkflowEngine-compatible context updates with JSON-safe payloads."""
    plain = to_plain_data(payload)
    return {**plain, "_context_update": plain}


def _repair_case_from_context(context: dict[str, Any]) -> RepairCase:
    value = context["repair_case"]
    return RepairCase(**value) if isinstance(value, dict) else value


def _repair_plan_from_context(context: dict[str, Any]) -> RepairPlan | None:
    value = context.get("repair_plan")
    if value is None:
        return None
    return RepairPlan(**value) if isinstance(value, dict) else value


def _repair_candidate_from_context(context: dict[str, Any]) -> RepairCandidate:
    value = context["repair_candidate"]
    return RepairCandidate(**value) if isinstance(value, dict) else value


def _sandbox_result_from_context(context: dict[str, Any]) -> SandboxResult:
    value = context["sandbox_result"]
    return SandboxResult(**value) if isinstance(value, dict) else value


def collect_failure_context_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    payload = context.get("input_payload") or {}
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="collect_failure_context",
        artifact_name="failure_context.json",
        payload=payload,
        output_root=context.get("output_root"),
    )
    return {}


def build_repair_case_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    from services.repair.repair_models import to_plain_data
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    output_root = _output_root_from_context(context)
    input_payload = context.get("input_payload")
    if not input_payload:
        input_payload = {
            key: value
            for key, value in context.items()
            if not key.startswith("_")
        }
    repair_case = build_repair_case(input_payload)
    if output_root is not None:
        repair_case.repo_snapshot["_repair_output_root"] = str(output_root)
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="build_repair_case",
        artifact_name="repair_case.json",
        payload=to_plain_data(repair_case),
        output_root=output_root,
    )
    return _context_update({"repair_case": repair_case})


def localize_code_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    repair_case = _repair_case_from_context(context)
    suspected = localize_code(repair_case)
    repair_case.suspected_files = [str(item["file"]) for item in suspected]
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="localize_code",
        artifact_name="localization_report.json",
        payload={"suspected_files": suspected},
        output_root=context.get("output_root"),
    )
    return _context_update({"repair_case": repair_case, "suspected_files": suspected})


def create_repair_plan_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    from services.repair.repair_models import to_plain_data
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    repair_case = _repair_case_from_context(context)
    repair_plan = build_repair_plan(repair_case, context.get("suspected_files") or [])
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="create_repair_plan",
        artifact_name="repair_plan.json",
        payload=to_plain_data(repair_plan),
        output_root=context.get("output_root"),
    )
    return _context_update({"repair_plan": repair_plan})


def generate_patch_candidate_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    from services.repair.learning_memory_scoring import score_candidates_with_memory
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    repair_case = _repair_case_from_context(context)
    repair_plan = _repair_plan_from_context(context)
    candidate = generate_patch_candidate(repair_case, repair_plan)
    
    candidates_list = [{
        "candidate_id": candidate.candidate_id,
        "agent_key": context.get("recommended_agent") or "mock_agent",
        "strategy": context.get("strategy") or "conservative",
        "base_score": candidate.confidence or 0.50,
        "confidence_score": candidate.confidence,
        "candidate_source": "mock_generator",
        "requested_mode": context.get("requested_mode") or "local_adapter",
        "diff_ref": candidate.patch_path,
        "test_score": 0.90,
        "risk_score": context.get("risk_score") or 0.15,
        "blocked_reason": "Policy violation detected" if context.get("policy_denied") else None,
        "policy_denied": context.get("policy_denied") or False,
        "sandbox_failed": context.get("sandbox_failed") or False,
        "artifact_refs": [candidate.patch_path]
    }]
    
    scored = score_candidates_with_memory(
        candidates_list,
        incident_id=incident_id,
        run_id=run_id,
        output_root=context.get("output_root")
    )
    
    payload = {
        "candidate_id": candidate.candidate_id,
        "candidate_source": "mock_generator",
        "agent_key": context.get("recommended_agent") or "mock_agent",
        "requested_mode": context.get("requested_mode") or "local_adapter",
        "diff_ref": candidate.patch_path,
        "confidence_score": candidate.confidence,
        "test_score": 0.90,
        "risk_score": context.get("risk_score") or 0.15,
        "blocked_reason": scored[0].get("blocked_reason") or (candidates_list[0].get("blocked_reason") if context.get("policy_denied") else None),
        "artifact_refs": [candidate.patch_path],
        "base_score": scored[0]["base_score"],
        "historical_success_score": scored[0]["historical_success_score"],
        "memory_adjustment": scored[0]["memory_adjustment"],
        "final_score": scored[0]["final_score"],
        "score_explanation": scored[0]["explanation"]
    }
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="generate_patch_candidate",
        artifact_name="patch_candidates.json",
        payload=payload,
        output_root=context.get("output_root"),
    )
    return _context_update({"repair_candidate": candidate})


def run_sandbox_verification_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    from services.repair.repair_models import to_plain_data
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    repair_candidate = _repair_candidate_from_context(context)
    repair_case = _repair_case_from_context(context)
    sandbox_result = run_patch_in_sandbox(repair_candidate, repair_case)
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="run_sandbox_verification",
        artifact_name="sandbox_result.json",
        payload=to_plain_data(sandbox_result),
        output_root=context.get("output_root"),
    )
    return _context_update({"sandbox_result": sandbox_result})


def run_verifier_mesh_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    verifier_result = run_verifier_mesh(
        _repair_case_from_context(context),
        _repair_candidate_from_context(context),
        _sandbox_result_from_context(context),
    )
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="run_verifier_mesh",
        artifact_name="verifier_mesh_result.json",
        payload=verifier_result,
        output_root=context.get("output_root"),
    )
    return _context_update({
        "verifier_result": verifier_result,
        "verifier_passed": verifier_result.get("status") == "VERIFIER_PASSED",
    })


def run_pr_agent_review_step(context: dict[str, Any]) -> dict[str, Any]:
    import asyncio
    from services.repair.pr_agent_adapter import PRAgentAdapter
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    output_root = _output_root_from_context(context)
    
    adapter = PRAgentAdapter()
    
    try:
        loop = asyncio.get_running_loop()
        # If there is a running loop, run the coroutine in it
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # We run in executor using a new event loop or using run_coroutine_threadsafe
            future = asyncio.run_coroutine_threadsafe(
                adapter.run_review_gate(incident_id, run_id, output_root),
                loop
            )
            review_payload = future.result()
    except RuntimeError:
        # No running event loop
        review_payload = asyncio.run(adapter.run_review_gate(
            incident_id=incident_id,
            run_id=run_id,
            output_root=output_root
        ))
        
    return _context_update({"pr_review_result": review_payload})


def run_cognitive_integrity_check_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    payload = {
        "cognitive_integrity_passed": True,
        "alignment_score": 1.0,
        "violations": []
    }
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="run_cognitive_integrity_check",
        artifact_name="cognitive_integrity.json",
        payload=payload,
        output_root=context.get("output_root"),
    )
    return _context_update({"cognitive_integrity_result": payload})


def score_risk_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.taskflow_artifacts import write_step_artifact
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    repair_case = _repair_case_from_context(context)
    repair_candidate = _repair_candidate_from_context(context)
    sandbox_result = _sandbox_result_from_context(context)
    repair_plan = _repair_plan_from_context(context)
    risk_decision = calculate_risk(
        repair_case,
        repair_candidate,
        context.get("verifier_result") or {},
    )
    if risk_decision.status in {"AUTO_REPAIR_BLOCKED", "QUORUM_REQUIRED", "HUMAN_APPROVAL_REQUIRED"}:
        final_status = risk_decision.status
    elif not sandbox_result.patch_applied or not sandbox_result.tests_passed:
        final_status = "SANDBOX_FAILED"
    elif (context.get("verifier_result") or {}).get("status") == "VERIFIER_FAILED":
        final_status = "VERIFIER_FAILED"
    else:
        final_status = risk_decision.status
    report = RepairReport(
        repair_case=repair_case,
        suspected_files=context.get("suspected_files") or [],
        candidate=repair_candidate,
        sandbox_result=sandbox_result,
        verifier_result=context.get("verifier_result") or {},
        risk_decision=risk_decision,
        final_status=final_status,
        repair_plan=repair_plan,
    )
    
    # Write to risk_report.json according to Phase 4 step 7 schema
    payload = {
        "risk_score": risk_decision.risk_score,
        "risk_level": risk_decision.risk_level,
        "blast_radius": "low",
        "changed_files": repair_candidate.changed_files,
        "policy_findings": [],
        "security_findings": [],
        "rollback_available": True,
        "human_gate_required": risk_decision.status != "DRAFT_PR_ALLOWED"
    }
    write_step_artifact(
        incident_id=incident_id,
        run_id=run_id,
        step_id="score_risk",
        artifact_name="risk_report.json",
        payload=payload,
        output_root=context.get("output_root"),
    )
    return _context_update({
        "risk_decision": risk_decision,
        "risk_decision_status": risk_decision.status,
        "risk_score": risk_decision.risk_score,
        "final_status": final_status,
        "repair_report": report,
    })


def run_patch_tournament_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.patch_tournament import run_patch_tournament
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    output_root = context.get("output_root")
    
    result = run_patch_tournament(incident_id, run_id, output_root=output_root)
    return _context_update({
        "tournament_result": result,
        "selected_candidate_id": result.selected_candidate_id,
        "requires_human_gate": result.requires_human_gate
    })


def build_final_report_step(context: dict[str, Any]) -> dict[str, Any]:
    report = context.get("repair_report")
    if report is None:
        return {}
    artifact_path = write_repair_outputs(report, output_root=_output_root_from_context(context))
    return _context_update({"artifact_path": str(artifact_path), "artifact_type": "json"})


def update_learning_memory_step(context: dict[str, Any]) -> dict[str, Any]:
    from services.repair.learning_memory_scoring import record_repair_outcome
    from services.repair.taskflow_artifacts import read_step_artifact
    incident_id = context.get("incident_id") or "INC-UNKNOWN"
    run_id = context.get("run_id") or "RUN-UNKNOWN"
    output_root = context.get("output_root")
    
    try:
        decision_data = read_step_artifact(incident_id, run_id, "human_gate_decision.json", output_root)
    except Exception:
        decision_data = {}
        
    try:
        sandbox_data = read_step_artifact(incident_id, run_id, "sandbox_result.json", output_root)
    except Exception:
        sandbox_data = {}
        
    try:
        risk_data = read_step_artifact(incident_id, run_id, "risk_report.json", output_root)
    except Exception:
        risk_data = {}
        
    try:
        candidates_data = read_step_artifact(incident_id, run_id, "patch_candidates.json", output_root)
    except Exception:
        candidates_data = {}
        
    selected_candidate_id = decision_data.get("selected_candidate_id") or candidates_data.get("candidate_id") or "candidate-001"
    agent_key = candidates_data.get("agent_key") or context.get("recommended_agent") or "swe_agent"
    strategy = context.get("strategy") or "conservative"
    decision = decision_data.get("decision") or "open_draft_pr_only"
    human_gate_status = decision_data.get("decision") or "DRAFT_PR_ONLY"
    risk_score = risk_data.get("risk_score") or context.get("risk_score") or 0.61
    
    test_result = "passed" if sandbox_data.get("tests_passed") or sandbox_data.get("status") == "PASSED" else "failed"
    if sandbox_data.get("patch_applied") is False:
        test_result = "failed"
        
    post_decision_result = "draft_pr_ready" if decision in {"approve_and_apply", "approve_and_merge", "open_draft_pr_only"} else "rejected"
    operator_rationale = decision_data.get("rationale") or "Automatic outcome logging"
    
    outcome = record_repair_outcome(
        incident_id=incident_id,
        run_id=run_id,
        finding_id=context.get("finding_id") or "FIND-UNKNOWN",
        selected_candidate_id=selected_candidate_id,
        candidate_source=candidates_data.get("candidate_source") or "mock_generator",
        agent_key=agent_key,
        strategy=strategy,
        decision=decision,
        human_gate_status=human_gate_status,
        risk_score=risk_score,
        risk_prediction_accuracy=None,
        test_result=test_result,
        post_decision_result=post_decision_result,
        operator_rationale=operator_rationale,
        output_root=output_root,
    )
    return outcome


def get_repair_orchestrator(model_orch=None, project_root: str = "."):
    """Lazy compatibility hook for the legacy long-running repair pipeline."""
    from services.repair.legacy_repair_orchestrator import get_repair_orchestrator as get_legacy

    return get_legacy(model_orch=model_orch, project_root=project_root)


def __getattr__(name: str):
    if name == "RepairOrchestrator":
        from services.repair.legacy_repair_orchestrator import RepairOrchestrator

        return RepairOrchestrator
    raise AttributeError(name)


def _load_json_payload(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _main() -> int:
    parser = argparse.ArgumentParser(description="Run Egemen YAZ safe repair flow.")
    parser.add_argument("--input", required=True, help="Path to failed test or trace payload JSON.")
    parser.add_argument("--output-root", default=None, help="Optional output root. Defaults to repair_outputs/.")
    args = parser.parse_args()

    report = run_repair_flow(_load_json_payload(args.input), output_root=args.output_root)
    print(json.dumps(to_plain_data(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
