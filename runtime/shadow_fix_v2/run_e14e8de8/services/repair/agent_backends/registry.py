"""Agent backend registry — selects and instantiates the active repair backend.

The backend is chosen via the ``REPAIR_AGENT_BACKEND`` environment variable:
- ``mock``       — Phase 1-3 mock (default, no LLM)
- ``agentless``  — LLM-only SEARCH/REPLACE patch generation
- ``mini_swe``   — Lightweight agent loop with sandbox shell execution

Usage::

    from services.repair.agent_backends.registry import get_backend
    backend = get_backend()
    result = backend.generate_patch(repair_case, work_dir="/tmp/sandbox")
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from services.repair.agent_backends.base import AgentBackend, AgentResult
from services.repair.evidence_pack import REPO_ROOT

logger = logging.getLogger(__name__)

_BACKENDS: dict[str, type] = {}


def _register_defaults() -> None:
    """Lazily register built-in backends on first access."""
    if _BACKENDS:
        return

    from services.repair.agent_backends.mock_backend import MockAgentBackend

    _BACKENDS["mock"] = MockAgentBackend
    from services.repair.agent_backends.deferred_backend import make_deferred_backend

    try:
        from services.repair.agent_backends.agentless_backend import AgentlessBackend

        _BACKENDS["agentless"] = AgentlessBackend
    except ImportError:
        logger.debug("agentless backend not available (missing deps)")

    from services.repair.agent_backends.safe_mini_swe_backend import SafeMiniSweBackend
    _BACKENDS["mini_swe"] = SafeMiniSweBackend

    try:
        from services.repair.agent_backends.open_swe_backend import OpenSWEAgentBackend
        _BACKENDS["open_swe"] = OpenSWEAgentBackend
    except ImportError:
        logger.debug("open_swe backend not available")

    if os.getenv("REPAIR_ENABLE_LEGACY_MINI_SWE", "").strip() != "1":
        logger.debug("legacy mini_swe backend disabled; safe mini_swe adapter registered")
        _BACKENDS["swe_agent"] = make_deferred_backend(
            "swe_agent",
            "SWE-agent-main.zip",
            "SWE-agent dogrudan calistirma yerine TaskFlow sandbox/verifier gate arkasina alinmali.",
        )
        _BACKENDS["live_swe"] = make_deferred_backend(
            "live_swe",
            "live-swe-agent-main.zip",
            "Canli SWE agent workflow'u ilk fazda sadece adapter noktasi olarak tutulur.",
        )
        _BACKENDS["openhands"] = make_deferred_backend(
            "openhands",
            "software-agent-sdk-main.zip",
            "OpenHands SDK gelismis workspace/tool katmani ucuncu faza birakildi.",
        )
        _BACKENDS["aider"] = make_deferred_backend(
            "aider",
            "aider-main.zip",
            "Aider diff workflow'u guvenli command/path policy olmadan dogrudan calistirilmaz.",
        )
        _BACKENDS["auto_code_rover"] = make_deferred_backend(
            "auto_code_rover",
            "auto-code-rover-main.zip",
            "AutoCodeRover multi-agent search/review deseni ileriki adapter olarak tutulur.",
        )
        _BACKENDS["repair_agent"] = make_deferred_backend(
            "repair_agent",
            "RepairAgent-main.zip",
            "RepairAgent APR stratejileri dogrudan patch uygulamadan once sandbox/verifier gerektirir.",
        )
        return

    try:
        from services.repair.agent_backends.mini_swe_backend import MiniSweAgentBackend

        _BACKENDS["legacy_mini_swe"] = MiniSweAgentBackend
    except ImportError:
        logger.debug("mini_swe backend not available (missing deps)")


def get_backend(
    name: str | None = None,
    repo_root: Path | None = None,
) -> AgentBackend:
    """Return the configured or named agent backend instance.

    Parameters
    ----------
    name:
        Explicit backend name.  If *None*, reads ``REPAIR_AGENT_BACKEND``
        env var, defaulting to ``"mock"``.
    repo_root:
        Repository root to pass to backends that need it.
    """
    _register_defaults()
    chosen = name or os.getenv("REPAIR_AGENT_BACKEND", "mock")
    cls = _BACKENDS.get(chosen)
    if cls is None:
        logger.warning("Unknown backend '%s', falling back to mock", chosen)
        cls = _BACKENDS["mock"]

    root = repo_root or REPO_ROOT
    # Backends accept repo_root if their __init__ supports it
    try:
        return cls(repo_root=root)  # type: ignore[call-arg]
    except TypeError:
        return cls()  # type: ignore[call-arg]


def list_backends() -> list[str]:
    """Return the names of all registered backends."""
    _register_defaults()
    return list(_BACKENDS.keys())
