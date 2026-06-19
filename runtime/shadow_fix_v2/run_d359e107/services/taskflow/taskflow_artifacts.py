from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from services.taskflow.taskflow_models import TaskArtifact, to_plain_data


def incident_output_dir(incident_id: str, output_root: str | Path | None = None) -> Path:
    root = Path(output_root) if output_root is not None else Path.cwd() / "repair_outputs"
    path = root / incident_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_artifact(
    incident_id: str,
    step_id: str,
    file_name: str,
    payload: Any,
    *,
    output_root: str | Path | None = None,
    artifact_type: str = "json",
) -> TaskArtifact:
    path = incident_output_dir(incident_id, output_root) / file_name
    path.write_text(json.dumps(to_plain_data(payload), indent=2, sort_keys=True), encoding="utf-8")
    return TaskArtifact(
        artifact_id=f"{step_id}:{file_name}",
        step_id=step_id,
        path=str(path),
        artifact_type=artifact_type,
        sha256=sha256_file(path),
    )


def artifact_for_existing_file(step_id: str, path: str | Path, artifact_type: str) -> TaskArtifact:
    file_path = Path(path)
    return TaskArtifact(
        artifact_id=f"{step_id}:{file_path.name}",
        step_id=step_id,
        path=str(file_path),
        artifact_type=artifact_type,
        sha256=sha256_file(file_path) if file_path.exists() else "",
    )
