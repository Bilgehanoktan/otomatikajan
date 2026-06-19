from __future__ import annotations

import json
from pathlib import Path

from services.repair.evidence_pack import REPO_ROOT
from services.repair.repair_models import RepairCase, RepairPlan, RepairReport, SandboxResult, to_plain_data


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_plain_data(payload), indent=2, sort_keys=True), encoding="utf-8")


def write_repair_outputs(
    repair_report: RepairReport,
    *,
    output_root: Path | None = None,
) -> Path:
    root = output_root or REPO_ROOT / "repair_outputs"
    incident_dir = root / repair_report.repair_case.incident_id
    incident_dir.mkdir(parents=True, exist_ok=True)

    write_json(incident_dir / "repair_case.json", repair_report.repair_case)
    if repair_report.repair_plan is not None:
        write_json(incident_dir / "repair_plan.json", repair_report.repair_plan)
    write_json(incident_dir / "repair_report.json", repair_report)
    write_sandbox_log(incident_dir / "sandbox.log", repair_report.sandbox_result)
    write_summary(incident_dir / "repair_summary.md", repair_report)
    return incident_dir / "repair_report.json"


def write_case(repair_case: RepairCase, *, output_root: Path | None = None) -> Path:
    root = output_root or REPO_ROOT / "repair_outputs"
    path = root / repair_case.incident_id / "repair_case.json"
    write_json(path, repair_case)
    return path


def write_plan(repair_plan: RepairPlan, repair_case: RepairCase, *, output_root: Path | None = None) -> Path:
    root = output_root or REPO_ROOT / "repair_outputs"
    path = root / repair_case.incident_id / "repair_plan.json"
    write_json(path, repair_plan)
    return path


def write_sandbox_log(path: Path, sandbox_result: SandboxResult) -> None:
    path.write_text(
        "\n".join(
            [
                f"patch_applied={sandbox_result.patch_applied}",
                f"tests_passed={sandbox_result.tests_passed}",
                f"exit_code={sandbox_result.exit_code}",
                f"duration_seconds={sandbox_result.duration_seconds}",
                "failed_commands=" + ", ".join(sandbox_result.failed_commands),
                "",
                "STDOUT:",
                sandbox_result.stdout,
                "",
                "STDERR:",
                sandbox_result.stderr,
            ]
        ),
        encoding="utf-8",
    )


def write_summary(path: Path, repair_report: RepairReport) -> None:
    decision = repair_report.risk_decision
    plan = repair_report.repair_plan
    lines = [
        f"# Repair Summary: {repair_report.repair_case.incident_id}",
        "",
        "## Hata Özeti",
        repair_report.repair_case.summary or "Özet sağlanmadı.",
        "",
        "## Şüpheli Dosyalar",
        *[f"- {item.get('file')} score={item.get('score')}" for item in repair_report.suspected_files],
        "",
        "## Repair Plan",
        plan.root_cause_hypothesis if plan else "Repair plan üretilmedi.",
        "",
        "## Sandbox Sonucu",
        f"- patch_applied: {repair_report.sandbox_result.patch_applied}",
        f"- tests_passed: {repair_report.sandbox_result.tests_passed}",
        f"- exit_code: {repair_report.sandbox_result.exit_code}",
        "",
        "## Verifier Sonucu",
        str(repair_report.verifier_result.get("status")),
        "",
        "## Risk Kararı",
        f"- status: {decision.status}",
        f"- risk_score: {decision.risk_score}",
        f"- recommended_action: {decision.recommended_action}",
        "",
        "## Önerilen Aksiyon",
        decision.recommended_action,
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
