import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from services.project_factory.models import ProjectIndexEntry, ArchiveIndex
from services.project_factory.artifacts import _resolve_project_factory_root, write_archive_index

def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def rebuild_archive_index(workspace_root: Optional[str] = None) -> ArchiveIndex:
    root = _resolve_project_factory_root(workspace_root)
    
    projects: List[ProjectIndexEntry] = []
    
    total_projects = 0
    closed_projects = 0
    active_projects = 0
    blocked_projects = 0
    revision_requested = 0
    
    if root.exists() and root.is_dir():
        for entry in root.iterdir():
            if entry.is_dir():
                # Potential project dir
                project_id = entry.name
                brief_path = entry / "project_brief.json"
                if not brief_path.exists():
                    continue  # Not a valid project dir or missing brief
                
                brief_data = _safe_load_json(brief_path)
                if not brief_data:
                    continue
                
                status = brief_data.get("status", "UNKNOWN")
                title = brief_data.get("title", "Untitled Project")
                
                # Fetch final decision
                final_decision_data = _safe_load_json(entry / "final_operator_decision.json")
                final_decision_str = final_decision_data.get("decision") if final_decision_data else None
                
                # Fetch release manifest
                release_path = entry / "release_archive" / "release_manifest.json"
                release_manifest_data = _safe_load_json(release_path)
                release_id = release_manifest_data.get("release_id") if release_manifest_data else None
                release_archive_path = str(entry / "release_archive").replace("\\", "/") if release_id else None
                
                # Risk and quality
                risk_level = None
                risk_score = None
                quality_score = None
                
                # Check candidate_review
                candidate_data = _safe_load_json(entry / "candidate_review.json")
                if candidate_data:
                    quality_score = candidate_data.get("quality_score")
                    risk_score = candidate_data.get("risk_score")
                
                # Check pr_review_report
                pr_review_data = _safe_load_json(entry / "pr_review_report.json")
                if pr_review_data:
                    if pr_review_data.get("quality_score") is not None:
                        quality_score = pr_review_data.get("quality_score")
                    if pr_review_data.get("risk_score") is not None:
                        risk_score = pr_review_data.get("risk_score")
                
                # Fetch risk level from risk_assessment if available
                risk_data = _safe_load_json(entry / "risk_assessment.json")
                if risk_data:
                    risk_level = risk_data.get("risk_level")
                
                # Basic metrics logic
                total_projects += 1
                if status == "PROJECT_CLOSED":
                    closed_projects += 1
                elif "BLOCKED" in status or status == "PR_CREATION_BLOCKED":
                    blocked_projects += 1
                elif status == "FINAL_REVISION_REQUESTED" or status == "REVISION_REQUESTED":
                    revision_requested += 1
                else:
                    active_projects += 1
                
                project_entry = ProjectIndexEntry(
                    project_id=project_id,
                    title=title,
                    status=status,
                    release_id=release_id,
                    final_decision=final_decision_str,
                    risk_level=risk_level,
                    quality_score=quality_score,
                    risk_score=risk_score,
                    release_archive_path=release_archive_path,
                    detail_url=f"/project-factory/{project_id}",
                    created_at=datetime.fromtimestamp(brief_path.stat().st_ctime, tz=timezone.utc).isoformat(),
                    updated_at=datetime.fromtimestamp(brief_path.stat().st_mtime, tz=timezone.utc).isoformat()
                )
                
                projects.append(project_entry)
                
    archive_index = ArchiveIndex(
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_projects=total_projects,
        closed_projects=closed_projects,
        active_projects=active_projects,
        blocked_projects=blocked_projects,
        revision_requested=revision_requested,
        projects=projects
    )
    
    write_archive_index(archive_index.model_dump(), workspace_root)
    return archive_index
