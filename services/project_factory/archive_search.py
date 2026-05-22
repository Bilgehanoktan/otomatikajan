import os
from typing import Optional, Dict, Any, List

from services.project_factory.models import ArchiveIndex, ProjectIndexEntry
from services.project_factory.artifacts import load_archive_index

def search_archive(
    query: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    has_release_archive: Optional[bool] = None,
    final_decision: Optional[str] = None,
    sort: str = "updated_at_desc",
    limit: int = 20,
    offset: int = 0,
    workspace_root: Optional[str] = None
) -> Dict[str, Any]:
    
    index_data = load_archive_index(workspace_root)
    if not index_data:
        return {"total": 0, "items": []}
    
    archive = ArchiveIndex(**index_data)
    results: List[ProjectIndexEntry] = archive.projects
    
    # Filtering
    if status:
        results = [p for p in results if p.status == status]
    if risk_level:
        results = [p for p in results if p.risk_level == risk_level]
    if final_decision:
        results = [p for p in results if p.final_decision == final_decision]
    if has_release_archive is not None:
        if has_release_archive:
            results = [p for p in results if p.release_id is not None]
        else:
            results = [p for p in results if p.release_id is None]
    if query:
        q = query.lower()
        results = [
            p for p in results 
            if q in p.project_id.lower() 
            or q in p.title.lower() 
            or (p.release_id and q in p.release_id.lower())
        ]
        
    # Sorting
    if sort == "updated_at_desc":
        results.sort(key=lambda x: x.updated_at, reverse=True)
    elif sort == "updated_at_asc":
        results.sort(key=lambda x: x.updated_at)
    elif sort == "quality_score_desc":
        results.sort(key=lambda x: x.quality_score or -1, reverse=True)
    elif sort == "risk_score_desc":
        results.sort(key=lambda x: x.risk_score or -1, reverse=True)
    elif sort == "status":
        results.sort(key=lambda x: x.status)
        
    total = len(results)
    
    # Pagination
    items = results[offset : offset + limit]
    
    return {
        "total": total,
        "items": [item.model_dump() for item in items]
    }
