from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def get_repo_snapshot(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    snapshot: dict[str, Any] = {"repo_root": str(root)}

    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        snapshot["branch"] = branch.stdout.strip()
    except Exception as exc:
        snapshot["branch_error"] = str(exc)

    try:
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        snapshot["head"] = head.stdout.strip()
    except Exception as exc:
        snapshot["head_error"] = str(exc)

    try:
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        snapshot["dirty"] = bool(status.stdout.strip())
    except Exception as exc:
        snapshot["dirty_error"] = str(exc)

    return snapshot


def recent_changed_files(repo_root: Path | None = None, limit: int = 40) -> list[str]:
    root = repo_root or REPO_ROOT
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return []

    files = [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]
    return files[:limit]
