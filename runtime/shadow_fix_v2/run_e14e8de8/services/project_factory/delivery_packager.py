from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from services.project_factory.artifacts import _resolve_project_dir

def build_delivery_package(
    project_id: str,
    operator_id: str,
    rationale: str,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Copies files from candidate_package/ to delivery_package/files/
    Generates delivery_manifest.json and release_notes.md.
    Sets production_apply_allowed = False.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    cand_dir = project_dir / "candidate_package"
    del_dir = project_dir / "delivery_package"

    # Enforce safe cleanup of previous delivery package
    if del_dir.exists():
        shutil.rmtree(del_dir, ignore_errors=True)
    del_dir.mkdir(parents=True, exist_ok=True)

    files_dest = del_dir / "files"
    files_dest.mkdir(parents=True, exist_ok=True)

    # 1. Load candidate manifests and reviews
    cand_manifest_path = project_dir / "candidate_manifest.json"
    if not cand_manifest_path.exists():
        raise FileNotFoundError(f"Missing candidate_manifest.json for project {project_id}")

    with open(cand_manifest_path, "r", encoding="utf-8") as f:
        cand_manifest = json.load(f)

    # Copy files
    files = cand_manifest.get("files", [])
    copied_files = []
    for f_info in files:
        rel_path = f_info.get("path")
        src_f = cand_dir / rel_path
        dest_f = files_dest / rel_path
        
        # Check path traversal
        if not str(dest_f.resolve()).startswith(str(files_dest.resolve())):
            continue

        if src_f.exists() and src_f.is_file():
            dest_f.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_f, dest_f)
            copied_files.append({
                "path": f"files/{rel_path}",
                "checksum": f_info.get("checksum")
            })

    # Copy metadata files into delivery_package
    metadata_files = [
        "candidate_manifest.json",
        "candidate_review.json",
        "risk_assessment.json",
        "quality_scorecard.json",
        "verification_report.json"
    ]
    for meta in metadata_files:
        src_meta = project_dir / meta
        if src_meta.exists():
            shutil.copy2(src_meta, del_dir / meta)

    # 2. Build delivery manifest
    delivery_id = f"DEL-{project_id}"
    candidate_id = cand_manifest.get("candidate_id", f"CAND-{project_id}")

    delivery_manifest = {
        "project_id": project_id,
        "delivery_id": delivery_id,
        "status": "DELIVERY_PACKAGE_READY",
        "approved_by": operator_id,
        "source_candidate_id": candidate_id,
        "files": copied_files,
        "review_refs": {
            "candidate_review": "candidate_review.json",
            "risk_assessment": "risk_assessment.json",
            "quality_scorecard": "quality_scorecard.json"
        },
        "production_apply_allowed": False
    }

    # Save manifest inside delivery package
    manifest_path = del_dir / "delivery_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(delivery_manifest, f, indent=2, ensure_ascii=False)

    # Also save delivery_manifest.json in project root directory as a convenience/artifact
    with open(project_dir / "delivery_manifest.json", "w", encoding="utf-8") as f:
        json.dump(delivery_manifest, f, indent=2, ensure_ascii=False)

    # 3. Create release_notes.md
    release_notes_path = del_dir / "release_notes.md"
    release_notes_content = f"""# Release Notes — {delivery_id}

## Delivery Details
- **Project ID:** {project_id}
- **Delivery ID:** {delivery_id}
- **Source Candidate ID:** {candidate_id}
- **Operator Approver:** {operator_id}

## Rationale
{rationale}

## Scope Packaged
The following sandbox output deliverables are packaged safely and locked in this delivery package:
"""
    for f_info in files:
        release_notes_content += f"- `{f_info.get('path')}` (SHA256 Checksum: `{f_info.get('checksum')}`)\n"

    release_notes_content += """
---
> [!IMPORTANT]
> **Delivery Lock:** This package is finalized for operator delivery. Direct production applying is strictly disabled (`production_apply_allowed = false`).
"""

    with open(release_notes_path, "w", encoding="utf-8") as f:
        f.write(release_notes_content)

    # Copy release notes to project root too
    with open(project_dir / "release_notes.md", "w", encoding="utf-8") as f:
        f.write(release_notes_content)

    return delivery_manifest

def load_delivery_manifest(
    project_id: str,
    workspace_root: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Loads delivery_manifest.json from the delivery_package directory if it exists.
    """
    project_dir = _resolve_project_dir(project_id, workspace_root)
    manifest_path = project_dir / "delivery_package" / "delivery_manifest.json"
    if not manifest_path.exists():
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)
