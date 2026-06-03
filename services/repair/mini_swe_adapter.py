from __future__ import annotations

import hashlib
import os
from pathlib import Path

from services.repair.evidence_pack import REPO_ROOT
from services.repair.repair_models import RepairCandidate, RepairCase, RepairPlan


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "repair_prompt.md"


def _output_dir(repair_case: RepairCase) -> Path:
    configured_output_root = (repair_case.repo_snapshot or {}).get("_repair_output_root")
    output_root = Path(configured_output_root) if configured_output_root else REPO_ROOT / "repair_outputs"
    output_dir = output_root / repair_case.incident_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_repair_prompt(repair_case: RepairCase, repair_plan: RepairPlan | None = None) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
    suspected = "\n".join(f"- {item}" for item in repair_case.suspected_files) or "- none"
    plan_text = ""
    if repair_plan is not None:
        plan_text = "\n".join(
            [
                f"Repair plan id: {repair_plan.repair_plan_id}",
                f"Root cause hypothesis: {repair_plan.root_cause_hypothesis}",
                "Target files:",
                *[f"- {path}" for path in repair_plan.target_files],
                "Expected tests:",
                *[f"- {cmd}" for cmd in repair_plan.expected_tests],
            ]
        )
    return template.format(
        incident_id=repair_case.incident_id,
        error_type=repair_case.error_type,
        summary=repair_case.summary,
        failed_command=repair_case.failed_command,
        failed_test=repair_case.failed_test,
        suspected_files=suspected,
        traceback=repair_case.traceback,
        repair_plan=plan_text,
    )


def generate_with_mini_swe(repair_case: RepairCase, repair_plan: RepairPlan | None = None) -> RepairCandidate:
    mode = os.getenv("MINI_SWE_MODE", "mock").strip().lower()
    output_dir = _output_dir(repair_case)
    prompt = build_repair_prompt(repair_case, repair_plan)
    (output_dir / "repair_prompt.rendered.md").write_text(prompt, encoding="utf-8")
    trajectory_path = output_dir / "agent_trajectory.log"
    patch_path = output_dir / "patch.diff"

    simulated_patch = repair_case.repo_snapshot.get("simulated_patch") if repair_case.repo_snapshot else None
    if mode == "real":
        trajectory_path.write_text(
            "MINI_SWE_MODE=real requested, but external mini-swe-agent execution is not enabled in Phase 1.\n",
            encoding="utf-8",
        )
        patch_path.write_text("", encoding="utf-8")
        changed_files: list[str] = []
        confidence = 0.15
        summary = "[DISABLED] mini-swe-agent real mode is configured but disabled by Phase 1 safety policy."
        candidate_status = "DISABLED"
    elif simulated_patch:
        trajectory_path.write_text("Mock mode used payload repo_snapshot.simulated_patch.\n", encoding="utf-8")
        patch_path.write_text(str(simulated_patch), encoding="utf-8")
        changed_files = list(repair_plan.target_files if repair_plan else repair_case.suspected_files)
        confidence = 0.45
        summary = "[SIMULATED] Simulated patch supplied by payload repo_snapshot.simulated_patch."
        candidate_status = "SIMULATED"
    else:
        trajectory_path.write_text("MINI_SWE_MODE=mock generated no code changes.\n", encoding="utf-8")
        patch_path.write_text("", encoding="utf-8")
        changed_files = []
        confidence = 0.1
        summary = "[NO_PROVIDER] No autonomous patch generated in mock mode; prompt prepared for future mini-swe-agent execution."
        candidate_status = "NO_PROVIDER"

    digest = hashlib.sha256(f"{repair_case.incident_id}:{prompt}:{mode}".encode("utf-8")).hexdigest()[:12]
    return RepairCandidate(
        candidate_id=f"RC-{digest}",
        patch_path=str(patch_path),
        changed_files=changed_files,
        agent_summary=summary,
        commands_run=[],
        confidence=confidence,
        status=candidate_status,
    )

