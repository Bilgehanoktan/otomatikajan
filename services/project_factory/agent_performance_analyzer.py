import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from services.project_factory.models import ArchiveIndex, AgentPerformance
from services.project_factory.artifacts import _resolve_project_factory_root

def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def analyze_agent_performance(archive: ArchiveIndex, workspace_root: Optional[str] = None) -> List[AgentPerformance]:
    root = _resolve_project_factory_root(workspace_root)
    
    # agent -> {uses, successes, blocked, failures}
    stats: Dict[str, Dict[str, Any]] = {}
    
    for project in archive.projects:
        pid = project.project_id
        project_dir = root / pid
        
        # Determine agent
        agent = "unknown"
        run_data = _safe_load_json(project_dir / "implementation_run.json")
        if run_data:
            agent = run_data.get("executor_agent", "unknown")
            
        if agent not in stats:
            stats[agent] = {
                "uses": 0, "successes": 0, "blocked": 0, "failures": []
            }
            
        st = stats[agent]
        st["uses"] += 1
        
        if project.status == "PROJECT_CLOSED" or project.final_decision == "FINAL_APPROVED":
            st["successes"] += 1
            
        if "BLOCKED" in project.status or project.final_decision == "FINAL_REJECTED":
            st["blocked"] += 1
            if project.status == "PR_CREATION_BLOCKED":
                st["failures"].append("pr_creation_failure")
            if project.status == "PR_REVIEW_BLOCKED":
                st["failures"].append("pr_review_failure")
                
        # Also check pr_review_report warnings for common failures
        pr_rev = _safe_load_json(project_dir / "pr_review_report.json")
        if pr_rev:
            if pr_rev.get("status") == "PR_REVIEW_BLOCKED":
                st["failures"].append("risk_acknowledgement_missing")
                
    results = []
    for agt, st in stats.items():
        if st["uses"] == 0:
            continue
            
        success_rate = round(st["successes"] / st["uses"], 2)
        failures = list(set(st["failures"]))
        
        results.append(AgentPerformance(
            agent=agt,
            uses=int(st["uses"]),
            success_rate=success_rate,
            blocked_count=int(st["blocked"]),
            common_failure_modes=failures
        ))
        
    results.sort(key=lambda x: x.uses, reverse=True)
    return results
