from typing import Optional, Dict, Any
from services.project_factory.models import RebuildArchiveRequest
from services.project_factory.archive_indexer import rebuild_archive_index
from services.project_factory.portfolio_metrics import generate_portfolio_metrics
from services.project_factory.archive_index_logs import log_rebuild_action

def rebuild_portfolio(request: RebuildArchiveRequest, workspace_root: Optional[str] = None) -> Dict[str, Any]:
    # 1. Rebuild Index
    archive = rebuild_archive_index(workspace_root)
    
    # 2. Generate Metrics
    metrics = generate_portfolio_metrics(workspace_root)
    
    # 3. Log Action
    log_rebuild_action(
        operator_id=request.operator_id,
        rationale=request.rationale,
        total_projects=archive.total_projects,
        release_archive_count=metrics.release_archive_count,
        workspace_root=workspace_root
    )
    
    return {
        "status": "success",
        "archive_summary": {
            "generated_at": archive.generated_at,
            "total_projects": archive.total_projects,
            "closed": archive.closed_projects
        },
        "metrics_summary": metrics.model_dump()
    }
