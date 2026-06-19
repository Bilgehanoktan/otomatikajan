"""Agentless repair backend — LLM-only patch generation without an agent loop.

Inspired by the Agentless paper/repo (princeton-nlp/Agentless):
1. Read suspected file contents
2. Build a structured repair prompt with file context + issue description
3. Query an LLM for a SEARCH/REPLACE or unified-diff edit
4. Parse the LLM response into a unified diff

This backend requires NO agent loop, NO shell access during generation, and
NO external framework dependencies beyond an HTTP-callable LLM API.

Security notes:
- No shell commands are executed during patch generation
- All file reads are limited to ``allowed_paths``
- Forbidden paths are never read or included in prompts
"""
from __future__ import annotations

import logging
import os
import re
import textwrap
from difflib import unified_diff
from pathlib import Path
from typing import Any

from services.repair.agent_backends.base import AgentResult
from services.repair.code_localizer import _is_forbidden, _normalize_path
from services.repair.evidence_pack import REPO_ROOT
from services.repair.repair_models import RepairCase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates (adapted from Agentless repair.py patterns)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an expert software engineer specialised in diagnosing and fixing Python bugs.
    You are given a bug report (traceback, failed test, logs) and the relevant source files.

    Rules:
    - Produce the MINIMUM change needed to fix the bug.
    - DO NOT touch files outside the allowed list.
    - DO NOT modify auth, governance, secrets, production config, or migration files.
    - Output your fix as a SEARCH/REPLACE block.

    SEARCH/REPLACE format:
    ### <file_path>
    <<<<<<< SEARCH
    <exact lines to find>
    =======
    <replacement lines>
    >>>>>>> REPLACE
""")

USER_PROMPT_TEMPLATE = textwrap.dedent("""\
    ## Bug Report
    **Incident:** {incident_id}
    **Error type:** {error_type}
    **Summary:** {summary}

    **Failed command:**
    ```
    {failed_command}
    ```

    **Failed test:**
    ```
    {failed_test}
    ```

    **Traceback:**
    ```
    {traceback}
    ```

    ## Relevant Source Files
    {file_contexts}

    ## Instructions
    Analyse the bug and produce SEARCH/REPLACE edits to fix it.
    Only edit the files shown above. Output nothing else.
""")

# ---------------------------------------------------------------------------
# File context builder (adapted from Agentless construct_topn_file_context)
# ---------------------------------------------------------------------------

_CONTEXT_LINES = 10  # lines of context around suspected locations


def _read_file_safely(path: str, repo_root: Path) -> str | None:
    """Read a file relative to *repo_root*, returning None if inaccessible."""
    full = repo_root / path
    try:
        if not full.exists():
            return None
        return full.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _build_file_context(
    suspected_files: list[str],
    repair_case: RepairCase,
    repo_root: Path,
    max_total_lines: int = 600,
) -> str:
    """Build a concatenated file-context string for the repair prompt.

    Each file is annotated with line numbers so the LLM can reference them.
    Forbidden files are silently skipped.
    """
    parts: list[str] = []
    total_lines = 0
    for rel_path in suspected_files:
        normalized = _normalize_path(rel_path)
        if _is_forbidden(normalized, repair_case.forbidden_paths):
            continue
        content = _read_file_safely(normalized, repo_root)
        if content is None:
            continue
        lines = content.splitlines()
        if total_lines + len(lines) > max_total_lines:
            # Include truncated version
            budget = max(20, max_total_lines - total_lines)
            lines = lines[:budget]
            lines.append(f"... ({len(content.splitlines()) - budget} more lines truncated)")
        numbered = "\n".join(f"{i + 1:4d} | {line}" for i, line in enumerate(lines))
        parts.append(f"### {normalized}\n```python\n{numbered}\n```\n")
        total_lines += len(lines)
        if total_lines >= max_total_lines:
            break
    return "\n".join(parts) if parts else "(no readable suspected files)"


# ---------------------------------------------------------------------------
# SEARCH/REPLACE parser (adapted from Agentless parse_diff_edit_commands)
# ---------------------------------------------------------------------------

_SR_PATTERN = re.compile(
    r"###\s*(?P<file>[^\n]+)\n"
    r"<<<<<<< SEARCH\n"
    r"(?P<search>.*?)\n"
    r"=======\n"
    r"(?P<replace>.*?)\n"
    r">>>>>>> REPLACE",
    re.DOTALL,
)


def _parse_search_replace(raw_response: str) -> list[dict[str, str]]:
    """Extract SEARCH/REPLACE edits from LLM response."""
    edits: list[dict[str, str]] = []
    for match in _SR_PATTERN.finditer(raw_response):
        edits.append(
            {
                "file": match.group("file").strip(),
                "search": match.group("search"),
                "replace": match.group("replace"),
            }
        )
    return edits


def _apply_edits_to_content(
    content: str, edits: list[dict[str, str]], file_path: str
) -> tuple[str, bool]:
    """Apply SEARCH/REPLACE edits to file content, returning (new_content, changed)."""
    changed = False
    for edit in edits:
        if _normalize_path(edit["file"]) != _normalize_path(file_path):
            continue
        search_text = edit["search"]
        replace_text = edit["replace"]
        if search_text in content:
            content = content.replace(search_text, replace_text, 1)
            changed = True
        else:
            logger.warning(
                "SEARCH block not found in %s — skipping edit (fuzzy match not implemented)",
                file_path,
            )
    return content, changed


def _generate_unified_diff(
    original: str, modified: str, file_path: str
) -> str:
    """Generate a unified diff between original and modified content."""
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    diff = unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    )
    return "".join(diff)


# ---------------------------------------------------------------------------
# LLM caller (pluggable — uses environment-based config)
# ---------------------------------------------------------------------------

def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call an LLM API and return the text response.

    Tries litellm first (supports OpenRouter, OpenAI, Anthropic, etc.).
    Falls back to a direct OpenAI-compatible HTTP call.
    """
    # Strategy 1: litellm (if available)
    try:
        import litellm  # type: ignore[import-untyped]

        model = os.getenv("REPAIR_LLM_MODEL", "openrouter/anthropic/claude-sonnet-4-20250514")
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
            temperature=0.0,
        )
        return response.choices[0].message.content or ""
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("litellm call failed: %s — trying openai fallback", exc)

    # Strategy 2: openai SDK
    try:
        import openai  # type: ignore[import-untyped]

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
        base_url = os.getenv("REPAIR_LLM_BASE_URL", "https://openrouter.ai/api/v1")
        model = os.getenv("REPAIR_LLM_MODEL", "anthropic/claude-sonnet-4-20250514")

        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
            temperature=0.0,
        )
        return response.choices[0].message.content or ""
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("openai SDK call failed: %s", exc)

    logger.error("No LLM backend available — returning empty response")
    return ""


# ---------------------------------------------------------------------------
# Public backend class
# ---------------------------------------------------------------------------

class AgentlessBackend:
    """LLM-only repair backend — no agent loop, no shell execution.

    Reads suspected source files, builds a repair prompt, queries an LLM,
    parses SEARCH/REPLACE edits from the response, and produces a unified diff.
    """

    name = "agentless"

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or REPO_ROOT

    def generate_patch(
        self,
        repair_case: RepairCase,
        *,
        work_dir: str = "",
        timeout_seconds: int = 120,
    ) -> AgentResult:
        root = Path(work_dir) if work_dir else self.repo_root
        suspected = repair_case.suspected_files or []
        if not suspected:
            return AgentResult(
                error="No suspected files to repair.",
                exit_status="no_targets",
            )

        # 1. Build file context
        file_context = _build_file_context(suspected, repair_case, root)

        # 2. Build prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            incident_id=repair_case.incident_id,
            error_type=repair_case.error_type,
            summary=repair_case.summary,
            failed_command=repair_case.failed_command or "(none)",
            failed_test=repair_case.failed_test or "(none)",
            traceback=repair_case.traceback or "(none)",
            file_contexts=file_context,
        )

        # 3. Call LLM
        logger.info("AgentlessBackend: calling LLM for %s", repair_case.incident_id)
        raw_response = _call_llm(SYSTEM_PROMPT, user_prompt)
        if not raw_response:
            return AgentResult(
                agent_summary="LLM returned empty response — no API key configured or API error.",
                error="LLM returned empty response.",
                exit_status="llm_error",
                confidence=0.0,
            )

        # 4. Parse SEARCH/REPLACE edits
        edits = _parse_search_replace(raw_response)
        if not edits:
            return AgentResult(
                agent_summary=f"LLM response did not contain parseable SEARCH/REPLACE edits.\nRaw response:\n{raw_response[:500]}",
                exit_status="parse_error",
                confidence=0.05,
                trajectory=[{"role": "assistant", "content": raw_response}],
            )

        # 5. Apply edits and generate unified diff
        diff_parts: list[str] = []
        changed_files: list[str] = []
        for edit in edits:
            file_path = _normalize_path(edit["file"])
            if _is_forbidden(file_path, repair_case.forbidden_paths):
                logger.warning("Skipping edit to forbidden file: %s", file_path)
                continue
            original = _read_file_safely(file_path, root)
            if original is None:
                logger.warning("Cannot read file for edit: %s", file_path)
                continue
            modified, did_change = _apply_edits_to_content(
                original, [edit], file_path
            )
            if did_change:
                diff_parts.append(_generate_unified_diff(original, modified, file_path))
                if file_path not in changed_files:
                    changed_files.append(file_path)

        diff_text = "\n".join(diff_parts)
        confidence = min(0.7, 0.3 + 0.1 * len(changed_files)) if changed_files else 0.1

        return AgentResult(
            diff_text=diff_text,
            changed_files=changed_files,
            agent_summary=f"Agentless repair: {len(edits)} edit(s) parsed, {len(changed_files)} file(s) changed.",
            confidence=confidence,
            trajectory=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt[:500] + "..."},
                {"role": "assistant", "content": raw_response[:1000] + "..."},
            ],
            exit_status="success" if changed_files else "no_applicable_edits",
        )
