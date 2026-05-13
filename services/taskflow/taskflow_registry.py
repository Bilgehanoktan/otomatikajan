from __future__ import annotations

from pathlib import Path


def list_workflows(workflow_dir: str | Path = "workflows") -> list[str]:
    root = Path(workflow_dir)
    if not root.exists():
        return []
    return sorted(path.stem for path in root.glob("*.yaml"))


def workflow_exists(workflow_name: str, workflow_dir: str | Path = "workflows") -> bool:
    candidate = Path(workflow_name)
    if candidate.exists():
        return True
    name = workflow_name if workflow_name.endswith(".yaml") else f"{workflow_name}.yaml"
    return (Path(workflow_dir) / name).exists()
