import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from services.project_factory.models import ArchiveIndex, RiskPattern
from services.project_factory.artifacts import _resolve_project_factory_root

def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def mine_risk_patterns(archive: ArchiveIndex, workspace_root: Optional[str] = None) -> List[RiskPattern]:
    root = _resolve_project_factory_root(workspace_root)
    
    pattern_counts: Dict[str, int] = {}
    pattern_projects: Dict[str, List[str]] = {}
    pattern_severities: Dict[str, str] = {}
    
    for project in archive.projects:
        pid = project.project_id
        project_dir = root / pid
        if not project_dir.exists():
            continue
            
        # 1. Check for block states in status
        if "BLOCKED" in project.status:
            pat = f"status_{project.status.lower()}"
            pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
            pattern_projects.setdefault(pat, []).append(pid)
            pattern_severities[pat] = "HIGH"
            
        # 2. Check for missing forbidden_actions in risk_assessment.json
        risk_data = _safe_load_json(project_dir / "risk_assessment.json")
        if risk_data:
            warnings = risk_data.get("warnings", [])
            for w in warnings:
                if "forbidden_actions" in str(w).lower():
                    pat = "missing_forbidden_action"
                    pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
                    pattern_projects.setdefault(pat, []).append(pid)
                    pattern_severities[pat] = "HIGH"
                    
            blockers = risk_data.get("blocking_risks", [])
            for b in blockers:
                if "path traversal" in str(b).lower():
                    pat = "path_traversal_block"
                    pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
                    pattern_projects.setdefault(pat, []).append(pid)
                    pattern_severities[pat] = "HIGH"
                elif "secret" in str(b).lower():
                    pat = "sandbox_skipped_secret"
                    pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
                    pattern_projects.setdefault(pat, []).append(pid)
                    pattern_severities[pat] = "HIGH"
                    
        # 3. Check for verification failures
        ver_data = _safe_load_json(project_dir / "verification_report.json")
        if ver_data:
            if not ver_data.get("all_tests_passed", True):
                pat = "verification_failure"
                pattern_counts[pat] = pattern_counts.get(pat, 0) + 1
                pattern_projects.setdefault(pat, []).append(pid)
                pattern_severities[pat] = "MEDIUM"
                
    # Transform to RiskPattern
    results = []
    for pat, count in pattern_counts.items():
        if count >= 2: # Only recurring (count >= 2)
            action = "Review agent logic"
            if pat == "missing_forbidden_action":
                action = "Strengthen external_agent_matrix forbidden_actions defaults."
            elif pat == "path_traversal_block":
                action = "Enhance path validation in sandbox artifacts."
            elif pat == "sandbox_skipped_secret":
                action = "Add stricter secret scanning filters."
                
            results.append(RiskPattern(
                pattern=pat,
                count=count,
                severity=pattern_severities[pat],
                affected_projects=pattern_projects[pat],
                recommended_action=action,
                suggested_workflow="self_repair_v1" if pattern_severities[pat] == "HIGH" else None
            ))
            
    # Sort by count desc
    results.sort(key=lambda x: x.count, reverse=True)
    return results
