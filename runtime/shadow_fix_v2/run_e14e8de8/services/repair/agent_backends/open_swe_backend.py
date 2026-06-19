"""Open-SWE-Agent backend — Optimized for UI and Frontend autonomous repairs.
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from services.repair.agent_backends.base import AgentResult
from services.repair.agent_backends.mini_swe_backend import (
    _call_llm_chat, _extract_commands, _check_submission, _execute_in_sandbox,
    MAX_STEPS
)
from services.repair.code_localizer import _is_forbidden, _normalize_path
from services.repair.evidence_pack import REPO_ROOT
from services.repair.repair_models import RepairCase

logger = logging.getLogger(__name__)

UI_SYSTEM_PROMPT = """\
You are an expert Frontend/UI Engineer fixing a bug in a React/Next.js/TypeScript project.
You have access to a bash shell in a sandboxed copy of the repository.

Rules:
1. Diagnose the issue by reading UI components (.tsx), styles (.css), and running tests.
2. Focus on visual consistency, responsiveness, and accessibility (WCAG).
3. Make the MINIMUM change to fix the bug.
4. DO NOT modify auth, governance, secrets, or production infrastructure.
5. After fixing, verify by running any relevant UI or unit tests.
6. When done, output EXACTLY: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT
   followed by the unified diff of your changes on the next line.

Available tools: bash commands only.
"""

UI_TASK_TEMPLATE = """\
## UI Bug Report
Incident: {incident_id}
Error: {error_type}
Summary: {summary}

Evidence Summary:
{ui_evidence_summary}

Suspected UI Files:
{suspected_files}

Working directory: {work_dir}

Please diagnose and fix this UI bug. Use the evidence provided (screenshots/logs) to guide your fix.
"""

class OpenSWEAgentBackend:
    """UI-optimized SWE-agent backend.
    """

    name = "open_swe_agent"

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or REPO_ROOT

    def generate_patch(
        self,
        repair_case: RepairCase,
        *,
        work_dir: str = "",
        timeout_seconds: int = 180,
    ) -> AgentResult:
        if not work_dir:
            # Enforce sandbox: Fail or create a temporary clone
            logger.error("OpenSWEAgentBackend: No work_dir provided. Sandbox execution is mandatory.")
            return AgentResult(
                diff_text="",
                changed_files=[],
                agent_summary="Error: No sandbox work_dir provided.",
                confidence=0.0,
                exit_status="blocked",
                error="Sandbox directory is required for safe execution."
            )
        
        sandbox_dir = work_dir
        suspected = "\n".join(f"- {f}" for f in repair_case.suspected_files) or "- none"
        
        # UI Evidence integration (if available in meta)
        ui_evidence = repair_case.context_data.get("ui_evidence", "No specific UI evidence captured.")
        
        started = time.monotonic()

        messages: list[dict[str, str]] = [
            {"role": "system", "content": UI_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": UI_TASK_TEMPLATE.format(
                    incident_id=repair_case.incident_id,
                    error_type=repair_case.error_type,
                    summary=repair_case.summary,
                    ui_evidence_summary=ui_evidence,
                    suspected_files=suspected,
                    work_dir=sandbox_dir,
                ),
            },
        ]

        trajectory: list[dict[str, Any]] = []
        commands_run: list[str] = []
        step = 0
        submission: str | None = None

        while step < MAX_STEPS:
            elapsed = time.monotonic() - started
            if elapsed > timeout_seconds:
                break

            response_text = _call_llm_chat(messages)
            if not response_text:
                break

            trajectory.append({"role": "assistant", "content": response_text, "step": step})
            messages.append({"role": "assistant", "content": response_text})

            submission = _check_submission(response_text)
            if submission is not None:
                break

            commands = _extract_commands(response_text)
            if not commands:
                messages.append({
                    "role": "user",
                    "content": "Please execute a bash command to proceed with the UI fix.",
                })
                step += 1
                continue

            observation_parts: list[str] = []
            for cmd in commands:
                commands_run.append(cmd)
                result = _execute_in_sandbox(cmd, sandbox_dir)
                observation_parts.append(
                    f"$ {cmd}\n{result['output']}\n[exit code: {result['returncode']}]"
                )

            observation = "\n\n".join(observation_parts)
            trajectory.append({"role": "observation", "content": observation, "step": step})
            messages.append({"role": "user", "content": observation})
            step += 1

        # Git diff extraction
        diff_text = ""
        changed_files: list[str] = []
        try:
            diff_result = subprocess.run(
                ["git", "diff", "--no-color"],
                cwd=sandbox_dir, capture_output=True, text=True, timeout=10, check=False
            )
            diff_text = diff_result.stdout.strip()
            if diff_text:
                files_result = subprocess.run(
                    ["git", "diff", "--name-only"],
                    cwd=sandbox_dir, capture_output=True, text=True, timeout=10, check=False
                )
                changed_files = [
                    _normalize_path(f)
                    for f in files_result.stdout.strip().splitlines()
                    if f.strip() and not _is_forbidden(_normalize_path(f), repair_case.forbidden_paths)
                ]
        except Exception as exc:
            logger.warning("OpenSWEAgentBackend: diff failed: %s", exc)

        if not diff_text and submission:
            diff_text = submission

        confidence = min(0.85, 0.4 + 0.1 * len(changed_files)) if changed_files else 0.4

        return AgentResult(
            diff_text=diff_text,
            changed_files=changed_files,
            agent_summary=f"Open-SWE-Agent (UI): {step} steps, {len(commands_run)} commands.",
            commands_run=commands_run,
            confidence=confidence,
            trajectory=trajectory,
            exit_status="submitted" if submission is not None else "completed",
        )
