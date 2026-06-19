from __future__ import annotations

from services.repair.agent_backends.base import AgentResult
from services.repair.mini_swe_adapter import generate_with_mini_swe
from services.repair.repair_models import RepairCase


class SafeMiniSweBackend:
    name = "mini_swe"

    def generate_patch(
        self,
        repair_case: RepairCase,
        *,
        work_dir: str = "",
        timeout_seconds: int = 120,
    ) -> AgentResult:
        candidate = generate_with_mini_swe(repair_case)
        diff_text = ""
        try:
            diff_text = open(candidate.patch_path, encoding="utf-8").read()
        except OSError:
            diff_text = ""
        return AgentResult(
            diff_text=diff_text,
            changed_files=candidate.changed_files,
            agent_summary=candidate.agent_summary,
            commands_run=candidate.commands_run,
            confidence=candidate.confidence,
            exit_status="safe_mini_swe_adapter",
        )

