from __future__ import annotations

import os
import json
import shutil
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from services.project_factory.artifacts import _resolve_project_dir
from services.project_factory.template_registry import get_template_config

def calculate_checksum(file_path: Path) -> str:
    """
    Computes SHA256 checksum for a file.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def package_candidate(
    project_id: str,
    template_name: str,
    verification_status: str,
    test_commands: List[str],
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Copies verified scaffold files to candidate_package/ and writes candidate_manifest.json.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    sandbox_dir = (project_dir / "sandbox").resolve()
    candidate_dir = (project_dir / "candidate_package").resolve()

    # Safety checks
    if not str(candidate_dir).startswith(str(project_dir)):
        raise ValueError("Candidate package destination outside project folder path")

    # Clean existing candidate directory if any
    if candidate_dir.exists():
        shutil.rmtree(candidate_dir, ignore_errors=True)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    config = get_template_config(template_name, workspace_root)
    allowed_outputs = config.get("allowed_outputs", []) if config else []

    packaged_files = []

    for rel_path in allowed_outputs:
        src_file = (sandbox_dir / rel_path).resolve()
        dest_file = (candidate_dir / rel_path).resolve()

        # Path traversal guard
        if not str(src_file).startswith(str(sandbox_dir)):
            continue
        if not str(dest_file).startswith(str(candidate_dir)):
            continue

        if src_file.exists() and src_file.is_file():
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)

            packaged_files.append({
                "path": rel_path,
                "checksum": calculate_checksum(src_file)
            })

    candidate_id = f"CAND-{project_id}"
    
    manifest = {
        "project_id": project_id,
        "candidate_id": candidate_id,
        "status": "CANDIDATE_READY",
        "files": packaged_files,
        "tests": {
            "status": verification_status,
            "commands": test_commands
        },
        "known_limitations": [
            "Strictly sandbox-evaluated; no production deployment has been performed."
        ],
        "requires_human_gate": True
    }

    # Write candidate_manifest.json
    manifest_path = project_dir / "candidate_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest

def load_candidate_manifest(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Loads candidate_manifest.json if exists.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    manifest_path = project_dir / "candidate_manifest.json"
    if not manifest_path.exists():
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)
