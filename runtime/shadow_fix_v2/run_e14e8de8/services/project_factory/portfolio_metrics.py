import os
from typing import Optional

from services.project_factory.models import ArchiveIndex, PortfolioMetrics
from services.project_factory.artifacts import load_archive_index, write_portfolio_metrics

def generate_portfolio_metrics(workspace_root: Optional[str] = None) -> PortfolioMetrics:
    index_data = load_archive_index(workspace_root)
    if not index_data:
        metrics = PortfolioMetrics()
        write_portfolio_metrics(metrics.model_dump(), workspace_root)
        return metrics

    archive_index = ArchiveIndex(**index_data)
    
    total = archive_index.total_projects
    by_status = {}
    by_risk_level = {}
    
    total_quality = 0
    projects_with_quality = 0
    total_risk = 0
    projects_with_risk = 0
    
    release_archive_count = 0
    open_human_gates = 0
    blocked_count = archive_index.blocked_projects
    
    for p in archive_index.projects:
        # Status aggregation
        if p.status not in by_status:
            by_status[p.status] = 0
        by_status[p.status] += 1
        
        # Risk level aggregation
        risk_lvl = p.risk_level or "UNKNOWN"
        if risk_lvl not in by_risk_level:
            by_risk_level[risk_lvl] = 0
        by_risk_level[risk_lvl] += 1
        
        # Averages
        if p.quality_score is not None:
            total_quality += p.quality_score
            projects_with_quality += 1
            
        if p.risk_score is not None:
            total_risk += p.risk_score
            projects_with_risk += 1
            
        # Counters
        if p.release_id:
            release_archive_count += 1
            
        if "WAITING" in p.status or "READY_FOR" in p.status:
            open_human_gates += 1
            
    avg_q = round(total_quality / projects_with_quality, 1) if projects_with_quality > 0 else 0.0
    avg_r = round(total_risk / projects_with_risk, 1) if projects_with_risk > 0 else 0.0
    
    metrics = PortfolioMetrics(
        total_projects=total,
        by_status=by_status,
        by_risk_level=by_risk_level,
        average_quality_score=avg_q,
        average_risk_score=avg_r,
        release_archive_count=release_archive_count,
        open_human_gates=open_human_gates,
        blocked_count=blocked_count
    )
    
    write_portfolio_metrics(metrics.model_dump(), workspace_root)
    return metrics
