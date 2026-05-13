"""Agent backends for patch generation.

This package provides pluggable agent backends that can be used by the
patch_candidate_runner to produce real diffs instead of mock placeholders.

Architecture inspired by:
- mini-swe-agent: lightweight agent loop with local/docker environments
- Agentless: LLM-only fault localization and repair (no agent loop)
- RepairAgent: state-machine driven iterative repair cycle
- SWE-ReX: sandboxed runtime execution

All backends implement the ``AgentBackend`` protocol defined in ``base.py``.
"""
