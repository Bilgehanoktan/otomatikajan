import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from services.project_factory.models import ArchiveIndex, TemplatePerformance
from services.project_factory.artifacts import _resolve_project_factory_root

def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def analyze_template_performance(archive: ArchiveIndex, workspace_root: Optional[str] = None) -> List[TemplatePerformance]:
    root = _resolve_project_factory_root(workspace_root)
    
    # template_name -> {uses, closed, sum_q, count_q, sum_r, count_r}
    stats: Dict[str, Dict[str, float]] = {}
    
    for project in archive.projects:
        pid = project.project_id
        project_dir = root / pid
        
        # Determine template
        template = "unknown"
        run_data = _safe_load_json(project_dir / "implementation_run.json")
        if run_data and "sandbox" in run_data:
            template = run_data["sandbox"].get("scaffold_template", "unknown")
            
        if template not in stats:
            stats[template] = {
                "uses": 0, "successes": 0, "sum_q": 0, "count_q": 0, "sum_r": 0, "count_r": 0
            }
            
        st = stats[template]
        st["uses"] += 1
        
        if project.status == "PROJECT_CLOSED" or project.final_decision == "FINAL_APPROVED":
            st["successes"] += 1
            
        if project.quality_score is not None:
            st["sum_q"] += project.quality_score
            st["count_q"] += 1
            
        if project.risk_score is not None:
            st["sum_r"] += project.risk_score
            st["count_r"] += 1
            
    results = []
    for tmpl, st in stats.items():
        if st["uses"] == 0:
            continue
            
        success_rate = round(st["successes"] / st["uses"], 2)
        avg_q = round(st["sum_q"] / st["count_q"], 1) if st["count_q"] > 0 else 0.0
        avg_r = round(st["sum_r"] / st["count_r"], 1) if st["count_r"] > 0 else 0.0
        
        results.append(TemplatePerformance(
            template=tmpl,
            uses=int(st["uses"]),
            success_rate=success_rate,
            average_quality_score=avg_q,
            average_risk_score=avg_r
        ))
        
    results.sort(key=lambda x: x.uses, reverse=True)
    return results
