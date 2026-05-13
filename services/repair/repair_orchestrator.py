from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from services.repair.code_localizer import localize_code
from services.repair.patch_candidate_runner import generate_patch_candidate
from services.repair.repair_case_builder import build_repair_case
from services.repair.repair_plan_builder import build_repair_plan
from services.repair.repair_models import RepairReport, to_plain_data
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


def build_repair_case_step(context: dict[str, Any]) -> dict[str, Any]:
    output_root = _output_root_from_context(context)
    repair_case = build_repair_case(context["input_payload"])
    if output_root is not None:
        repair_case.repo_snapshot["_repair_output_root"] = str(output_root)
    artifact_path = write_case(repair_case, output_root=output_root)
    return {"repair_case": repair_case, "artifact_path": str(artifact_path), "artifact_type": "json"}


def localize_code_step(context: dict[str, Any]) -> dict[str, Any]:
    repair_case = context["repair_case"]
    suspected = localize_code(repair_case)
    repair_case.suspected_files = [str(item["file"]) for item in suspected]
    return {"repair_case": repair_case, "suspected_files": suspected}


def create_repair_plan_step(context: dict[str, Any]) -> dict[str, Any]:
    repair_case = context["repair_case"]
    repair_plan = build_repair_plan(repair_case, context.get("suspected_files") or [])
    artifact_path = write_plan(repair_plan, repair_case, output_root=_output_root_from_context(context))
    return {"repair_plan": repair_plan, "artifact_path": str(artifact_path), "artifact_type": "json"}


def generate_patch_candidate_step(context: dict[str, Any]) -> dict[str, Any]:
    candidate = generate_patch_candidate(context["repair_case"], context.get("repair_plan"))
    return {"repair_candidate": candidate, "artifact_path": candidate.patch_path, "artifact_type": "diff"}


def run_sandbox_verification_step(context: dict[str, Any]) -> dict[str, Any]:
    sandbox_result = run_patch_in_sandbox(context["repair_candidate"], context["repair_case"])
    output_root = _output_root_from_context(context)
    root = output_root or Path.cwd() / "repair_outputs"
    path = root / context["repair_case"].incident_id / "sandbox.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_sandbox_log(path, sandbox_result)
    return {"sandbox_result": sandbox_result, "artifact_path": str(path), "artifact_type": "log"}


def run_verifier_mesh_step(context: dict[str, Any]) -> dict[str, Any]:
    verifier_result = run_verifier_mesh(
        context["repair_case"],
        context["repair_candidate"],
        context["sandbox_result"],
    )
    return {
        "verifier_result": verifier_result,
        "verifier_passed": verifier_result.get("status") == "VERIFIER_PASSED",
    }


def score_risk_step(context: dict[str, Any]) -> dict[str, Any]:
    risk_decision = calculate_risk(
        context["repair_case"],
        context["repair_candidate"],
        context.get("verifier_result") or {},
    )
    if risk_decision.status in {"AUTO_REPAIR_BLOCKED", "QUORUM_REQUIRED", "HUMAN_APPROVAL_REQUIRED"}:
        final_status = risk_decision.status
    elif not context["sandbox_result"].patch_applied or not context["sandbox_result"].tests_passed:
        final_status = "SANDBOX_FAILED"
    elif (context.get("verifier_result") or {}).get("status") == "VERIFIER_FAILED":
        final_status = "VERIFIER_FAILED"
    else:
        final_status = risk_decision.status
    report = RepairReport(
        repair_case=context["repair_case"],
        suspected_files=context.get("suspected_files") or [],
        candidate=context["repair_candidate"],
        sandbox_result=context["sandbox_result"],
        verifier_result=context.get("verifier_result") or {},
        risk_decision=risk_decision,
        final_status=final_status,
        repair_plan=context.get("repair_plan"),
    )
    artifact_path = write_repair_outputs(report, output_root=_output_root_from_context(context))
    return {
        "risk_decision": risk_decision,
        "risk_decision_status": risk_decision.status,
        "risk_score": risk_decision.risk_score,
        "final_status": final_status,
        "repair_report": report,
        "artifact_path": str(artifact_path),
        "artifact_type": "json",
    }


def build_final_report_step(context: dict[str, Any]) -> dict[str, Any]:
    report = context.get("repair_report")
    if report is None:
        return {}
    artifact_path = write_repair_outputs(report, output_root=_output_root_from_context(context))
    return {"artifact_path": str(artifact_path), "artifact_type": "json"}


def update_learning_memory_step(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "learning_memory_status": "SKIPPED",
        "learning_memory_reason": "Learning Memory scoring ikinci faza bırakıldı.",
    }


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
