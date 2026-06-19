"""Base protocol and types for agent backends.

Every agent backend implements ``AgentBackend.generate_patch`` which receives a
``RepairCase`` and returns an ``AgentResult`` containing the generated diff text,
changed files, and execution metadata.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from services.repair.repair_models import RepairCase

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Outcome produced by an agent backend."""

    diff_text: str = ""
    """Unified diff text suitable for ``git apply``."""

    changed_files: list[str] = field(default_factory=list)
    """Relative paths of files the diff touches."""

    agent_summary: str = ""
    """Human-readable explanation of what the agent did."""

    commands_run: list[str] = field(default_factory=list)
    """Shell commands the agent executed during its run."""

    confidence: float = 0.0
    """Agent self-reported confidence (0.0 – 1.0)."""

    trajectory: list[dict[str, Any]] = field(default_factory=list)
    """Full agent trajectory for audit/debugging."""

    cost: float = 0.0
    """Estimated API cost in USD."""

    exit_status: str = ""
    """Backend-specific exit status string."""

    error: str = ""
    """Non-empty if the run failed."""


@runtime_checkable
class AgentBackend(Protocol):
    """Protocol that all agent backends must satisfy."""

    name: str

    def generate_patch(
        self,
        repair_case: RepairCase,
        *,
        work_dir: str = "",
        timeout_seconds: int = 120,
    ) -> AgentResult:
        """Generate a patch for the given repair case.

        Parameters
        ----------
        repair_case:
            The repair case including traceback, suspected files, etc.
        work_dir:
            Working directory (typically a sandbox copy).
        timeout_seconds:
            Maximum wall-clock time allowed for the agent run.

        Returns
        -------
        AgentResult with the generated diff and metadata.
        """
        ...
