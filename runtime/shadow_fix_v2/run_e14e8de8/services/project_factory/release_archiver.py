"""
Release Archiver.

Orchestrates the creation of the complete release archive:
  1. Evidence bundle
  2. Closure report
  3. Release manifest
"""
from __future__ import annotations

from typing import Optional
from services.project_factory.artifacts import (
    _resolve_project_dir,
    write_release_manifest,
    _load_json_artifact,
)
from services.project_factory.models import ReleaseManifest
from services.project_factory.evidence_bundle import build_evidence_bundle
from services.project_factory.closure_reporter import generate_closure_report


def build_release_archive(
    project_id: str,
    release_id: str,
    operator_id: str,
    rationale: str,
    workspace_root: Optional[str] = None,
) -> ReleaseManifest:
    """
    Builds the complete release archive for a finally approved project.
    """
    # 1. Build evidence bundle
    copied, missing = build_evidence_bundle(project_id, workspace_root)

    # 2. Generate closure report
    generate_closure_report(
        project_id=project_id,
        operator_id=operator_id,
        rationale=rationale,
        release_id=release_id,
        copied_evidence=copied,
        missing_evidence=missing,
        workspace_root=workspace_root,
    )

    # 3. Copy final_operator_decision into archive
    project_dir = _resolve_project_dir(project_id, workspace_root)
    archive_dir = project_dir / "release_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    fod_src = project_dir / "final_operator_decision.json"
    if fod_src.exists():
        import shutil
        shutil.copy2(fod_src, archive_dir / "final_operator_decision.json")

    # 4. Build release manifest
    manifest = ReleaseManifest(
        project_id=project_id,
        release_id=release_id,
        status="RELEASE_ARCHIVE_READY",
        final_decision="FINAL_APPROVED",
        approved_by=operator_id,
        production_apply_performed=False,
        merge_performed=False,
        deploy_performed=False,
        evidence_count=len(copied),
        closure_report="closure_report.md",
    )

    write_release_manifest(project_id, manifest.model_dump(), workspace_root)
    return manifest
