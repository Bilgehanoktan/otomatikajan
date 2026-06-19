from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

from services.repair.evidence_pack import REPO_ROOT
from services.repair.mini_swe_adapter import generate_with_mini_swe
from services.repair.repair_models import RepairCandidate, RepairCase, RepairPlan

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "repair_prompt.md"


def build_repair_prompt(repair_case: RepairCase, repair_plan: RepairPlan | None = None) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""
    suspected = "\n".join(f"- {item}" for item in repair_case.suspected_files) or "- none"
    plan_text = ""
    if repair_plan is not None:
        plan_text = "\n".join(
            [
                f"repair_plan_id: {repair_plan.repair_plan_id}",
                f"root_cause_hypothesis: {repair_plan.root_cause_hypothesis}",
                "target_files:",
                *[f"- {path}" for path in repair_plan.target_files],
                "expected_tests:",
                *[f"- {command}" for command in repair_plan.expected_tests],
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


def generate_patch_candidate(
    repair_case: RepairCase,
    repair_plan: RepairPlan | None = None,
    *,
    backend_name: str | None = None,
) -> RepairCandidate:
    """Generate a repair patch candidate using the configured agent backend.

    The backend is selected via:
    1. Explicit ``backend_name`` parameter
    2. ``REPAIR_AGENT_BACKEND`` environment variable
    3. Default: ``"mock"`` (Phase 1-3 empty diff)

    Supported backends:
    - ``mock``:      Empty diff / simulated patch (no LLM call)
    - ``agentless``: LLM-only SEARCH/REPLACE patch generation
    - ``mini_swe``:  Lightweight agent loop with sandbox shell execution

    The function always writes prompt artifacts and returns a ``RepairCandidate``
    regardless of which backend is used.
    """
    configured_output_root = (repair_case.repo_snapshot or {}).get("_repair_output_root")
    output_root = Path(configured_output_root) if configured_output_root else REPO_ROOT / "repair_outputs"
    output_dir = output_root / repair_case.incident_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Always render and persist the repair prompt template
    prompt = build_repair_prompt(repair_case, repair_plan)
    (output_dir / "repair_prompt.rendered.md").write_text(prompt, encoding="utf-8")

    patch_path = output_dir / "patch.diff"

    # Dispatch to agent backend
    from services.repair.agent_backends.registry import get_backend

    chosen = backend_name or os.getenv("REPAIR_AGENT_BACKEND")
    if chosen is None and os.getenv("MINI_SWE_MODE"):
        chosen = "mini_swe"
    chosen = chosen or "mock"

    # Phase 32 Compliance - Validate execution via the External Agent Catalog
    built_in_backends = {"mock", "agentless", "mini_swe", "mini-swe", "mini_swe_agent"}
    
    if chosen not in built_in_backends:
        from services.repair.external_repo_integrations import validate_agent_execution
        from services.repair.external_agents.registry import ExternalAgentRegistry
        from services.repair.external_agents.models import ExternalAgentContext
        
        agent_key_map = {
            "swe_agent": "swe_agent",
            "swe_rex": "swe_rex",
            "pr_agent": "pr_agent",
            "stagehand": "stagehand",
            "openhands": "openhands",
            "github_copilot": "github_copilot",
        }
        
        agent_key = agent_key_map.get(chosen, chosen)
        mode_map = {
            "swe_agent": "local_adapter",
            "swe_rex": "sandbox_runner",
            "pr_agent": "review_gate",
            "stagehand": "local_adapter",
            "openhands": "experimental",
            "github_copilot": "local_adapter",
        }
        requested_mode = mode_map.get(agent_key, "local_adapter")
        
        validation = validate_agent_execution(agent_key, requested_mode)
        if not validation.get("valid", True) or validation.get("status") == "BLOCKED":
            logger.error("External Agent execution BLOCKED by Phase 32 safety catalog policy: %s", validation.get("reason"))
            raise PermissionError(f"Phase 32 External Agent Intake Policy Violation: {validation.get('reason')}")
        elif validation.get("status") == "WARNING_HIGH_RISK":
            logger.warning("Phase 32 External Agent Intake WARNING: %s", validation.get("reason"))

        # In Phase 1, if it's a registered external agent, invoke the adapter runtime layer
        try:
            adapter = ExternalAgentRegistry.get_adapter(agent_key)
            ctx = ExternalAgentContext(
                incident_id=repair_case.incident_id,
                repair_case_id=repair_case.incident_id,
                agent_key=agent_key,
                requested_mode=requested_mode,
                allowed_tools=repair_case.allowed_paths,
                forbidden_actions=validation.get("forbidden_actions", []),
                output_dir=str(output_root),
            )
            result = adapter.run(ctx)
            
            # In Phase 1, if the result is blocked or failed, do not generate candidate
            if result.status in {"BLOCKED", "FAILED"}:
                logger.error("External Agent execution returned failed status '%s': %s", result.status, result.blocked_reason)
                raise PermissionError(f"External agent execution returned non-successful status: {result.status}. Reason: {result.blocked_reason}")

            patch_file_path = result.output_artifact
            changed_files = ["services/repair/mock_dummy.py"] if agent_key == "swe_agent" else []
            
            digest = hashlib.sha256(
                f"{repair_case.incident_id}:{prompt}:{agent_key}".encode("utf-8")
            ).hexdigest()[:12]
            
            return RepairCandidate(
                candidate_id=f"RC-{digest}",
                patch_path=str(patch_file_path),
                changed_files=changed_files,
                agent_summary=f"External Agent '{agent_key}' completed successfully via adapter.",
                commands_run=["mock_search", "mock_replace"] if agent_key == "swe_agent" else [],
                confidence=result.confidence_score,
                status="PATCH_PROPOSED",
            )
        except PermissionError as pe:
            raise pe
        except Exception as e:
            logger.error("Error executing external agent adapter '%s': %s", agent_key, e)
            raise e

    if chosen in {"mini_swe", "mini-swe", "mini_swe_agent"}:
        return generate_with_mini_swe(repair_case, repair_plan)

    backend = get_backend(chosen)
    logger.info(
        "generate_patch_candidate: using backend '%s' for %s",
        backend.name,
        repair_case.incident_id,
    )

    agent_result = backend.generate_patch(
        repair_case,
        work_dir=str(output_root.parent) if chosen != "mock" else "",
        timeout_seconds=int(os.getenv("REPAIR_AGENT_TIMEOUT", "120")),
    )

    # Write diff artifact
    diff_text = agent_result.diff_text or ""
    patch_path.write_text(diff_text, encoding="utf-8")

    # Write trajectory for audit
    if agent_result.trajectory:
        trajectory_path = output_dir / "agent_trajectory.json"
        try:
            trajectory_path.write_text(
                json.dumps(agent_result.trajectory, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception:
            pass  # Non-critical

    changed_files = agent_result.changed_files or []
    confidence = agent_result.confidence
    summary = agent_result.agent_summary or f"Backend '{backend.name}' completed."

    digest = hashlib.sha256(
        f"{repair_case.incident_id}:{prompt}:{backend.name}".encode("utf-8")
    ).hexdigest()[:12]

    return RepairCandidate(
        candidate_id=f"RC-{digest}",
        patch_path=str(patch_path),
        changed_files=changed_files,
        agent_summary=summary,
        commands_run=agent_result.commands_run,
        confidence=confidence,
        status="PATCH_PROPOSED",
    )
