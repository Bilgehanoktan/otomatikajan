import os
import json
import pytest
from datetime import datetime, timezone

from services.project_factory.models import ArchiveIndex, ProjectIndexEntry
from services.project_factory.artifacts import write_archive_index
from services.project_factory.archive_search import search_archive

def test_archive_search(tmp_path):
    archive = ArchiveIndex(
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_projects=3,
        projects=[
            ProjectIndexEntry(
                project_id="PF-1",
                title="Apple Dashboard",
                status="PROJECT_CLOSED",
                risk_level="LOW",
                quality_score=90,
                release_id="REL-1",
                final_decision="FINAL_APPROVED",
                detail_url="/p1",
                created_at="time",
                updated_at="2026-05-20"
            ),
            ProjectIndexEntry(
                project_id="PF-2",
                title="Banana API",
                status="PR_CREATION_BLOCKED",
                risk_level="HIGH",
                quality_score=50,
                detail_url="/p2",
                created_at="time",
                updated_at="2026-05-21"
            ),
            ProjectIndexEntry(
                project_id="PF-3",
                title="Cherry UI",
                status="HUMAN_GATE_WAITING",
                risk_level="LOW",
                quality_score=100,
                detail_url="/p3",
                created_at="time",
                updated_at="2026-05-22"
            )
        ]
    )
    
    write_archive_index(archive.model_dump(), str(tmp_path))
    
    # 1. Search by status
    res = search_archive(status="PROJECT_CLOSED", workspace_root=str(tmp_path))
    assert res["total"] == 1
    assert res["items"][0]["project_id"] == "PF-1"
    
    # 2. Search by query
    res = search_archive(query="banana", workspace_root=str(tmp_path))
    assert res["total"] == 1
    assert res["items"][0]["project_id"] == "PF-2"
    
    # 3. Search by risk level
    res = search_archive(risk_level="LOW", workspace_root=str(tmp_path))
    assert res["total"] == 2
    
    # 4. Search by has_release_archive
    res = search_archive(has_release_archive=True, workspace_root=str(tmp_path))
    assert res["total"] == 1
    assert res["items"][0]["project_id"] == "PF-1"
    
    # 5. Sort by quality_score
    res = search_archive(sort="quality_score_desc", workspace_root=str(tmp_path))
    assert res["items"][0]["project_id"] == "PF-3"
    assert res["items"][2]["project_id"] == "PF-2"
    
    # 6. Pagination
    res = search_archive(limit=1, offset=1, sort="updated_at_asc", workspace_root=str(tmp_path))
    assert len(res["items"]) == 1
    assert res["items"][0]["project_id"] == "PF-2"
