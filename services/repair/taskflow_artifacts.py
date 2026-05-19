from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from services.taskflow.taskflow_models import to_plain_data


def artifact_dir_for_run(incident_id: str, run_id: str, output_root: str | Path | None = None) -> Path:
    root = Path(output_root) if output_root is not None else Path.cwd() / "repair_outputs"
    path = root / incident_id / "taskflow" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_step_artifact(
    incident_id: str,
    run_id: str,
    step_id: str,
    artifact_name: str,
    payload: Any,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    dir_path = artifact_dir_for_run(incident_id, run_id, output_root)
    file_path = dir_path / artifact_name
    plain_data = to_plain_data(payload)
    file_path.write_text(json.dumps(plain_data, indent=2, sort_keys=True), encoding="utf-8")
    sha = get_sha256(file_path)
    
    try:
        path_str = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        path_str = str(file_path)

    return {
        "step_id": step_id,
        "name": artifact_name,
        "path": path_str,
        "status": "written",
        "sha256": sha,
    }


def read_step_artifact(
    incident_id: str,
    run_id: str,
    artifact_name: str,
    output_root: str | Path | None = None,
) -> Any:
    dir_path = artifact_dir_for_run(incident_id, run_id, output_root)
    file_path = dir_path / artifact_name
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact {artifact_name} not found at {file_path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def validate_required_artifacts(
    incident_id: str,
    run_id: str,
    required_artifacts: list[str],
    output_root: str | Path | None = None,
) -> dict[str, str]:
    dir_path = artifact_dir_for_run(incident_id, run_id, output_root)
    missing = {}
    for name in required_artifacts:
        file_path = dir_path / name
        if not file_path.exists():
            missing[name] = "missing"
    return missing


def build_artifact_manifest(
    incident_id: str,
    run_id: str,
    workflow_id: str,
    steps_config: list[dict[str, Any]],
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    dir_path = artifact_dir_for_run(incident_id, run_id, output_root)
    artifacts_list = []
    for step in steps_config:
        step_id = step.get("id") or step.get("step_id")
        artifact_name = step.get("artifact")
        if not step_id or not artifact_name:
            continue
        file_path = dir_path / artifact_name
        if file_path.exists():
            sha = get_sha256(file_path)
            status = "written"
        else:
            sha = ""
            status = "missing"
        
        try:
            path_str = str(file_path.relative_to(Path.cwd()))
        except ValueError:
            path_str = str(file_path)
            
        artifacts_list.append({
            "step_id": step_id,
            "name": artifact_name,
            "path": path_str,
            "status": status,
            "sha256": sha,
        })
    
    # Scan and include auxiliary JSON artifacts
    known_auxiliary = [
        ("candidate_memory_score.json", "score_risk"),
        ("strategy_success_profile.json", "update_learning_memory"),
        ("learning_memory_update.json", "update_learning_memory")
    ]
    for name, step_id in known_auxiliary:
        # Check if already included to avoid duplicates
        if any(a["name"] == name for a in artifacts_list):
            continue
        file_path = dir_path / name
        if file_path.exists():
            sha = get_sha256(file_path)
            try:
                path_str = str(file_path.relative_to(Path.cwd()))
            except ValueError:
                path_str = str(file_path)
            artifacts_list.append({
                "step_id": step_id,
                "name": name,
                "path": path_str,
                "status": "written",
                "sha256": sha,
            })
            
    manifest = {
        "incident_id": incident_id,
        "run_id": run_id,
        "workflow_id": workflow_id,
        "artifacts": artifacts_list,
    }
    
    manifest_path = dir_path / "artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest
