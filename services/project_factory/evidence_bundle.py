"""
Evidence Bundle Builder.

Copies all required evidence artifacts into release_archive/evidence_bundle/.
Returns a list of successfully copied files and any missing artifacts.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from services.project_factory.artifacts import _resolve_project_dir

REQUIRED_EVIDENCE_FILES = [
    "project_brief.json",
    "requirement_gate.json",
    "sandbox_manifest.json",
    "implementation_run.json",
    "implementation_report.json",
    "verification_report.json",
    "candidate_manifest.json",
    "candidate_review.json",
    "risk_assessment.json",
    "quality_scorecard.json",
    "delivery_manifest.json",
    "apply_preview.json",
    "diff_summary.md",
    "draft_pr_plan.json",
    "draft_pr_creation.json",
    "pr_review_report.json",
    "pr_agent_review.json",
    "verifier_mesh_report.json",
    "pr_review_scorecard.json",
]


def build_evidence_bundle(
    project_id: str,
    workspace_root: Optional[str] = None,
) -> Tuple[List[str], List[str]]:
    """
    Copies evidence artifacts into release_archive/evidence_bundle/.
    Returns (copied_files, missing_files).
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    bundle_dir = project_dir / "release_archive" / "evidence_bundle"

    if bundle_dir.exists():
        shutil.rmtree(bundle_dir, ignore_errors=True)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    copied: List[str] = []
    missing: List[str] = []

    for filename in REQUIRED_EVIDENCE_FILES:
        src = project_dir / filename
        dest = bundle_dir / filename

        if src.exists() and src.is_file():
            # Path traversal safety
            if not str(dest.resolve()).startswith(str(bundle_dir.resolve())):
                missing.append(filename)
                continue
            shutil.copy2(src, dest)
            copied.append(filename)
        else:
            missing.append(filename)

    return copied, missing
