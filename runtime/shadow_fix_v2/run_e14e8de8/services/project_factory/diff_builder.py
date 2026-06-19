from __future__ import annotations

import difflib
from pathlib import Path
from typing import Iterable, Dict, Any


def build_diff_summary(
    workspace_root: str,
    delivery_files_dir: Path,
    file_changes: Iterable[Dict[str, Any]],
) -> str:
    root = Path(workspace_root).resolve()
    sections = ["# Apply Preview Diff Summary", ""]

    for change in file_changes:
        rel_path = change["path"]
        source_path = delivery_files_dir / rel_path
        target_path = root / rel_path
        source_lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        target_lines = []
        if target_path.exists() and target_path.is_file():
            target_lines = target_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

        diff = difflib.unified_diff(
            target_lines,
            source_lines,
            fromfile=f"workspace/{rel_path}",
            tofile=f"delivery/{rel_path}",
            lineterm="",
        )
        sections.append(f"## `{rel_path}`")
        sections.append("```diff")
        rendered = "\n".join(diff)
        sections.append(rendered if rendered else "# no textual diff")
        sections.append("```")
        sections.append("")

    return "\n".join(sections)
