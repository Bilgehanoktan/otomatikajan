"""Mock agent backend for Phase 1-3 testing.

Returns empty diffs or simulated patches supplied via ``repo_snapshot``.
This is the default backend used when no real agent is configured.
"""
from __future__ import annotations

import logging

from services.repair.agent_backends.base import AgentBackend, AgentResult
from services.repair.repair_models import RepairCase

logger = logging.getLogger(__name__)


class MockAgentBackend:
    """Placeholder backend that does not call any LLM or agent framework.

    It optionally uses ``repair_case.repo_snapshot["simulated_patch"]`` to
    return a pre-supplied diff for integration testing.
    """

    name = "mock"

    def generate_patch(
        self,
        repair_case: RepairCase,
        *,
        work_dir: str = "",
        timeout_seconds: int = 120,
    ) -> AgentResult:
        simulated = (repair_case.repo_snapshot or {}).get("simulated_patch")
        if simulated:
            logger.info("MockAgentBackend: using simulated_patch from repo_snapshot")
            return AgentResult(
                diff_text=str(simulated),
                changed_files=list(repair_case.suspected_files),
                agent_summary="Simulated patch from repo_snapshot.simulated_patch.",
                confidence=0.45,
                exit_status="simulated",
            )

        logger.info("MockAgentBackend: producing empty diff (no agent configured)")
        return AgentResult(
            diff_text="",
            changed_files=[],
            agent_summary="No autonomous patch generated; prompt prepared for future agent integration.",
            confidence=0.1,
            exit_status="mock_no_patch",
        )


# Convenience singleton
mock_backend = MockAgentBackend()
