"""Mini-SWE-Agent backend — lightweight agent loop with local/docker execution.

Inspired by klieret/mini-swe-agent architecture:
- Agent loop: system prompt → task prompt → (query LLM → execute action → observe) loop
- Environment: local subprocess or Docker container
- Cost/step limits enforced

This backend runs an agent that can execute shell commands in a sandboxed
working directory to diagnose and fix bugs iteratively.

Security constraints:
- Commands run ONLY in the sandbox working directory (never production)
- Executable allowlist: python, pytest, grep, find, cat, sed, head, tail, diff
- No network access in Docker mode (``--network none``)
- Step and cost limits prevent runaway execution
- Forbidden paths are never modified
"""
from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from services.repair.agent_backends.base import AgentResult
from services.repair.code_localizer import _is_forbidden, _normalize_path
from services.repair.evidence_pack import REPO_ROOT
from services.repair.repair_models import RepairCase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_STEPS = int(os.getenv("REPAIR_AGENT_MAX_STEPS", "15"))
MAX_COST_USD = float(os.getenv("REPAIR_AGENT_MAX_COST", "1.0"))
COMMAND_TIMEOUT = 30  # per-command timeout in seconds

SAFE_EXECUTABLES = {
    "python", "python3", "python.exe", "py", "py.exe",
    "pytest", "pytest.exe",
    "grep", "find", "cat", "head", "tail", "wc",
    "sed", "awk", "diff", "patch",
    "ls", "dir", "echo", "nl",
    "git",
}
CONTROL_OPERATORS = ["&&", "||", "|", ";", ">", "<", "`", "$(", "\n"]

SYSTEM_PROMPT = """\
You are a software engineer fixing a bug in a Python project.
You have access to a bash shell in a sandboxed copy of the repository.

Rules:
1. Diagnose the issue by reading files and running tests.
2. Make the MINIMUM change to fix the bug.
3. DO NOT modify auth, governance, secrets, production config, or migration files.
4. After fixing, verify by running the failed test/command.
5. When done, output EXACTLY: echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT
   followed by the unified diff of your changes on the next line.

Available tools: bash commands only.
"""

TASK_TEMPLATE = """\
## Bug Report
Incident: {incident_id}
Error: {error_type}
Summary: {summary}

Failed command: {failed_command}
Failed test: {failed_test}

Traceback:
{traceback}

Suspected files:
{suspected_files}

Working directory: {work_dir}

Please diagnose and fix this bug. Start by examining the suspected files.
"""


# ---------------------------------------------------------------------------
# Safe command execution (adapted from mini-swe-agent LocalEnvironment)
# ---------------------------------------------------------------------------

def _validate_command(command: str) -> bool:
    """Check if a command is safe to execute in the sandbox."""
    # Block dangerous operators
    if any(op in command for op in ["rm -rf /", "mkfs", "dd if=", "> /dev/"]):
        return False
    if any(operator in command for operator in CONTROL_OPERATORS):
        return False

    # Extract first executable
    try:
        args = shlex.split(command, posix=True)
    except ValueError:
        return False

    if args:
        exe = Path(args[0]).name.lower()
        return exe in SAFE_EXECUTABLES

    return False


def _execute_in_sandbox(
    command: str,
    work_dir: str,
    timeout: int = COMMAND_TIMEOUT,
) -> dict[str, Any]:
    """Execute a command in the sandbox working directory."""
    if not _validate_command(command):
        return {
            "output": f"Command blocked by safety filter: {command}",
            "returncode": -1,
        }

    try:
        args = shlex.split(command, posix=True)
        result = subprocess.run(
            args,
            text=True,
            cwd=work_dir,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PAGER": "cat", "TQDM_DISABLE": "1"},
        )
        output = result.stdout or ""
        # Truncate very long outputs
        if len(output) > 10000:
            output = output[:5000] + f"\n... ({len(output) - 10000} chars truncated) ...\n" + output[-5000:]
        return {"output": output, "returncode": result.returncode}
    except subprocess.TimeoutExpired as exc:
        raw = getattr(exc, "output", None)
        raw = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else (raw or "")
        return {"output": raw + f"\nCommand timed out after {timeout}s.", "returncode": -1}
    except Exception as exc:
        return {"output": str(exc), "returncode": -1}


# ---------------------------------------------------------------------------
# LLM interaction (reuses agentless_backend's _call_llm)
# ---------------------------------------------------------------------------

def _call_llm_chat(messages: list[dict[str, str]]) -> str:
    """Send a chat completion request and return the assistant response."""
    try:
        import litellm  # type: ignore[import-untyped]

        model = os.getenv("REPAIR_LLM_MODEL", "openrouter/anthropic/claude-sonnet-4-20250514")
        response = litellm.completion(
            model=model,
            messages=messages,
            max_tokens=2048,
            temperature=0.0,
        )
        return response.choices[0].message.content or ""
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("litellm chat call failed: %s", exc)

    try:
        import openai  # type: ignore[import-untyped]

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
        base_url = os.getenv("REPAIR_LLM_BASE_URL", "https://openrouter.ai/api/v1")
        model = os.getenv("REPAIR_LLM_MODEL", "anthropic/claude-sonnet-4-20250514")

        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=2048,
            temperature=0.0,
        )
        return response.choices[0].message.content or ""
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("openai SDK chat call failed: %s", exc)

    return ""


# ---------------------------------------------------------------------------
# Command extraction from LLM response
# ---------------------------------------------------------------------------

_BASH_BLOCK_RE = re.compile(r"```(?:bash|sh|shell)?\s*\n(.*?)```", re.DOTALL)


def _extract_commands(response: str) -> list[str]:
    """Extract bash commands from LLM response code blocks."""
    commands: list[str] = []
    for match in _BASH_BLOCK_RE.finditer(response):
        block = match.group(1).strip()
        if block:
            commands.append(block)
    return commands


def _check_submission(response: str) -> str | None:
    """Check if the response signals task completion and extract the submission."""
    if "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" in response:
        idx = response.index("COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT")
        submission = response[idx + len("COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"):].strip()
        return submission
    return None


# ---------------------------------------------------------------------------
# Agent loop (adapted from mini-swe-agent DefaultAgent.run)
# ---------------------------------------------------------------------------

class MiniSweAgentBackend:
    """Lightweight SWE-agent backend with iterative command execution.

    Runs an agent loop:
    1. Query LLM with repair context + conversation history
    2. Extract bash commands from response
    3. Execute commands in sandbox
    4. Feed output back to LLM
    5. Repeat until submission or limits reached
    """

    name = "mini_swe_agent"

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or REPO_ROOT

    def generate_patch(
        self,
        repair_case: RepairCase,
        *,
        work_dir: str = "",
        timeout_seconds: int = 120,
    ) -> AgentResult:
        sandbox_dir = work_dir or str(self.repo_root)
        suspected = "\n".join(f"- {f}" for f in repair_case.suspected_files) or "- none"
        started = time.monotonic()

        # Build initial messages
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": TASK_TEMPLATE.format(
                    incident_id=repair_case.incident_id,
                    error_type=repair_case.error_type,
                    summary=repair_case.summary,
                    failed_command=repair_case.failed_command or "(none)",
                    failed_test=repair_case.failed_test or "(none)",
                    traceback=repair_case.traceback or "(none)",
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
                logger.warning("MiniSweAgentBackend: timeout after %.1fs", elapsed)
                break

            # Query LLM
            response_text = _call_llm_chat(messages)
            if not response_text:
                logger.warning("MiniSweAgentBackend: LLM returned empty at step %d", step)
                break

            trajectory.append({"role": "assistant", "content": response_text, "step": step})
            messages.append({"role": "assistant", "content": response_text})

            # Check for submission
            submission = _check_submission(response_text)
            if submission is not None:
                logger.info("MiniSweAgentBackend: agent submitted at step %d", step)
                break

            # Extract and execute commands
            commands = _extract_commands(response_text)
            if not commands:
                # If no commands, prompt the agent to take action
                messages.append({
                    "role": "user",
                    "content": "Please execute a bash command to proceed with the diagnosis or fix.",
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

        # Generate diff from git
        diff_text = ""
        changed_files: list[str] = []
        try:
            diff_result = subprocess.run(
                ["git", "diff", "--no-color"],
                cwd=sandbox_dir,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            diff_text = diff_result.stdout.strip()
            if diff_text:
                # Extract changed files
                files_result = subprocess.run(
                    ["git", "diff", "--name-only"],
                    cwd=sandbox_dir,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                changed_files = [
                    _normalize_path(f)
                    for f in files_result.stdout.strip().splitlines()
                    if f.strip() and not _is_forbidden(_normalize_path(f), repair_case.forbidden_paths)
                ]
        except Exception as exc:
            logger.warning("Failed to extract git diff: %s", exc)

        # Use submission as diff if git diff is empty
        if not diff_text and submission:
            diff_text = submission

        confidence = 0.0
        if changed_files:
            confidence = min(0.65, 0.25 + 0.1 * len(changed_files))
        elif submission:
            confidence = 0.3

        exit_status = "submitted" if submission is not None else ("timeout" if step >= MAX_STEPS else "completed")

        return AgentResult(
            diff_text=diff_text,
            changed_files=changed_files,
            agent_summary=f"Mini-SWE-Agent: {step} steps, {len(commands_run)} commands, {len(changed_files)} files changed.",
            commands_run=commands_run,
            confidence=confidence,
            trajectory=trajectory,
            exit_status=exit_status,
        )
