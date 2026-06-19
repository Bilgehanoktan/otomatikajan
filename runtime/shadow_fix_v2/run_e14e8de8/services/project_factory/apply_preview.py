from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List

from services.project_factory.apply_safety import assess_delivery_file_safety
from services.project_factory.artifacts import _resolve_project_dir, write_apply_preview, load_apply_preview
from services.project_factory.delivery_packager import load_delivery_manifest
from services.project_factory.diff_builder import build_diff_summary
from services.project_factory.models import ApplyPreview, FileChange, ApplyPreviewRequest


def _manifest_relative_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    return normalized.removeprefix("files/")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_apply_preview(
    project_id: str,
    request: ApplyPreviewRequest,
    workspace_root: Optional[str] = None,
) -> Dict[str, Any]:
    if not request.risk_acknowledgement:
        raise ValueError("risk_acknowledgement is required to run apply preview.")

    project_dir = _resolve_project_dir(project_id, workspace_root)
    delivery_manifest = load_delivery_manifest(project_id, workspace_root)
    if not delivery_manifest:
        raise ValueError(f"No delivery_manifest found for {project_id}.")
    if delivery_manifest.get("production_apply_allowed", True) is not False:
        raise ValueError("delivery_manifest.production_apply_allowed must be False.")

    delivery_files_dir = project_dir / "delivery_package" / "files"
    file_changes: List[FileChange] = []
    blocking_risks: List[str] = []
    conflicts: List[str] = []
    root = Path(workspace_root or Path.cwd()).resolve()

    for entry in delivery_manifest.get("files", []):
        rel_path = _manifest_relative_path(entry.get("path", ""))
        source_file = (delivery_files_dir / rel_path).resolve()
        safety = assess_delivery_file_safety(rel_path, source_file)
        blocking_risks.extend(safety["blocking_risks"])

        target_file = (root / rel_path).resolve()
        target_exists = target_file.exists()
        file_changes.append(FileChange(
            path=rel_path,
            change_type="MODIFY" if target_exists else "ADD",
            risk=safety["risk"],
            source_hash=_sha256(source_file) if source_file.exists() else "",
            target_exists=target_exists,
        ))
        if target_exists and target_file.is_dir():
            conflicts.append(f"target path is directory: {rel_path}")

    add_count = sum(1 for c in file_changes if c.change_type == "ADD")
    modify_count = sum(1 for c in file_changes if c.change_type == "MODIFY")
    preview = ApplyPreview(
        project_id=project_id,
        status="APPLY_PREVIEW_BLOCKED" if blocking_risks else "APPLY_PREVIEW_READY",
        production_apply_performed=False,
        source_delivery_package="delivery_package",
        file_changes=file_changes,
        conflicts=conflicts,
        blocking_risks=blocking_risks,
        summary={"add": add_count, "modify": modify_count, "delete": 0},
    )

    preview_dict = preview.model_dump()
    write_apply_preview(project_id, preview_dict, workspace_root)
    diff_summary = build_diff_summary(workspace_root or str(Path.cwd()), delivery_files_dir, preview_dict["file_changes"])
    (project_dir / "diff_summary.md").write_text(diff_summary, encoding="utf-8")
    delivery_diff = project_dir / "delivery_package" / "diff_summary.md"
    delivery_diff.write_text(diff_summary, encoding="utf-8")
    return preview_dict


def get_apply_preview(project_id: str, workspace_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return load_apply_preview(project_id, workspace_root)
