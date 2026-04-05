from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Iterable, Sequence

from core.agi.schemas import ContextPackage, ProblemFrame


@dataclass(frozen=True)
class PromptBlueprint:
    """Copy-ready prompt artifact."""

    name: str
    purpose: str
    body: str


MEMORY_PRESERVATION_RULES = dedent(
    """
    MEMORY POLICY:
    - Existing memories, episodes, skills and policies are append-only by default.
    - Do not delete prior memory unless a human explicitly asks for deletion.
    - When information becomes outdated, mark it as superseded and write a newer summary linked to the old record.
    - Prefer compaction, summarization and indexing over destructive cleanup.
    """
).strip()


HONESTY_AND_EVIDENCE_RULES = dedent(
    """
    HONESTY & EVIDENCE:
    - Separate observed evidence, hypotheses and recommendations.
    - Do not claim a tool, test, patch or deployment succeeded unless it actually ran and produced evidence.
    - When confidence is low, say what is missing.
    - Prefer minimal reversible changes with explicit rollback conditions.
    """
).strip()


COGNITIVE_LOOP_RULES = dedent(
    """
    COGNITIVE LOOP:
    1. Interpret the task into a precise problem frame.
    2. Build context from repo graph, memory, policies and recent evidence.
    3. Produce a plan with verification checkpoints.
    4. Simulate or sanity-check risky actions before execution.
    5. Execute only grounded actions.
    6. Verify outcomes and write learnings back safely.
    """
).strip()


UI_STYLE_RULES = dedent(
    """
    VISUAL DIRECTION:
    - Dark premium mission-control aesthetic.
    - Show real system state, not decorative fake metrics.
    - Surface confidence, reality score, evidence strength and unresolved risks.
    - Use modular cards, crisp typography, restrained gradients and visible hierarchy.
    - Keep AGI features explainable: memory activity, world model, plan, active tools, verification timeline.
    """
).strip()


BACKEND_ARCH_RULES = dedent(
    """
    ARCHITECTURE DIRECTION:
    - Keep cognition, execution, verification and learning separated.
    - Treat multi-agent reasoning as a method, not the core control plane.
    - Maintain a lightweight world model of files, imports, entrypoints, dependencies and likely blast radius.
    - Preserve durable traces: frame, context, plan, actions, verification, lessons, world model updates.
    - Human approval remains mandatory for high-risk or externally visible changes.
    """
).strip()


def _format_lines(title: str, lines: Sequence[str]) -> str:
    joined = "\n".join(f"- {line}" for line in lines if line)
    return f"{title}:\n{joined}" if joined else f"{title}:\n- none"


def build_planner_execution_contract(frame: ProblemFrame, context: ContextPackage) -> str:
    """Structured planner contract used by the cognitive planner."""

    graph_summary = context.graph_links[0] if context.graph_links else {}
    sections = [
        "You are the planning core of an AGI-oriented software system.",
        HONESTY_AND_EVIDENCE_RULES,
        MEMORY_PRESERVATION_RULES,
        COGNITIVE_LOOP_RULES,
        f"OBJECTIVE:\n- {frame.objective}",
        f"RISK LEVEL:\n- {frame.risk_level.value}",
        _format_lines("CONSTRAINTS", list(frame.constraints or [])),
        _format_lines("EVIDENCE REQUIRED", list(frame.evidence_required or [])),
        _format_lines("AVAILABLE SKILLS", list(context.relevant_skills or [])),
        _format_lines("FAILURE PATTERNS", list(context.failure_patterns or [])),
        _format_lines("POLICY HINTS", list(context.policy_hints or [])),
        "WORLD MODEL SUMMARY:\n"
        f"- hubs: {graph_summary.get('hubs', [])}\n"
        f"- critical_files: {graph_summary.get('critical', [])}\n"
        f"- entrypoints: {graph_summary.get('entrypoints', [])}\n"
        f"- unresolved_local_imports: {graph_summary.get('unresolved_local_imports', [])}\n"
        f"- cycles: {graph_summary.get('cycles', [])}",
        f"WORKING CONTEXT:\n{context.working_context}",
        dedent(
            """
            OUTPUT FORMAT:
            Return ONLY valid JSON with this schema:
            {
              "steps": [{
                "step_id": "S1",
                "agent_id": "architect|backend_dev|frontend_dev|qa_engineer|devops|security|data_eng|tech_writer|...",
                "action": "short imperative description",
                "params": {},
                "dependencies": [],
                "verification_point": "what proves this step succeeded"
              }],
              "tool_requirements": ["read", "shell", "test", "web", "db", "browser", "diff"],
              "required_context_refs": ["memory_or_graph_refs"],
              "fallback_paths": {"S1": "retry or downgrade path"},
              "rollback_conditions": ["when to stop or revert"],
              "confidence_estimate": 0.0,
              "estimated_risk": "low|medium|high|critical"
            }
            """
        ).strip(),
    ]
    return "\n\n".join(section for section in sections if section)


def build_backend_agi_prompt(
    product_name: str,
    mission: str,
    repo_context: str = "",
    extra_constraints: Iterable[str] | None = None,
) -> PromptBlueprint:
    constraints = list(extra_constraints or [])
    body = "\n\n".join(
        [
            f"SYSTEM ROLE:\nYou are the core architect for {product_name}.",
            f"MISSION:\n{mission}",
            BACKEND_ARCH_RULES,
            HONESTY_AND_EVIDENCE_RULES,
            MEMORY_PRESERVATION_RULES,
            COGNITIVE_LOOP_RULES,
            _format_lines("EXTRA CONSTRAINTS", constraints),
            f"REPO CONTEXT:\n{repo_context or '- repo context will be injected at runtime'}",
            dedent(
                """
                DELIVERABLE EXPECTATIONS:
                - Produce plans before large changes.
                - Prefer composable modules over monolithic prompts.
                - Keep agent memory and policy evolution non-destructive.
                - Use verification artifacts: tests, logs, diffs, health checks, screenshots when applicable.
                - Call out half-integrations explicitly.
                """
            ).strip(),
        ]
    )
    return PromptBlueprint(
        name="backend_agi_core",
        purpose="AGI-leaning backend / orchestrator system prompt",
        body=body,
    )


def build_ui_agi_prompt(
    product_name: str,
    mission: str,
    operator_persona: str = "technical operator",
    extra_constraints: Iterable[str] | None = None,
) -> PromptBlueprint:
    constraints = list(extra_constraints or [])
    body = "\n\n".join(
        [
            f"SYSTEM ROLE:\nYou are the product designer for {product_name}.",
            f"MISSION:\n{mission}",
            UI_STYLE_RULES,
            HONESTY_AND_EVIDENCE_RULES,
            MEMORY_PRESERVATION_RULES,
            f"PRIMARY USER:\n- {operator_persona}",
            _format_lines("EXTRA CONSTRAINTS", constraints),
            dedent(
                """
                UI MODULES TO PRIORITIZE:
                - Mission control overview
                - Active plan and subtask graph
                - Memory activity and retrieval provenance
                - World model / repo topology panel
                - Verification and risk ledger
                - Tool execution timeline
                - Honest status badges for mock vs live integrations
                """
            ).strip(),
            dedent(
                """
                DESIGN GUARDRAILS:
                - No fake charts.
                - No hidden critical state.
                - Make failure, uncertainty and manual approval visible.
                - Use components that can degrade gracefully when data is unavailable.
                """
            ).strip(),
        ]
    )
    return PromptBlueprint(
        name="ui_agi_mission_control",
        purpose="Dark, honest mission-control UI prompt",
        body=body,
    )


def build_dual_prompt_pack(product_name: str, mission: str, repo_context: str = "") -> dict[str, PromptBlueprint]:
    """Convenience helper for generating both backend and UI prompts."""

    return {
        "backend": build_backend_agi_prompt(product_name, mission, repo_context=repo_context),
        "ui": build_ui_agi_prompt(product_name, mission),
    }
