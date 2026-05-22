import os
import json
import pytest
from datetime import datetime, timezone

from services.project_factory.models import ArchiveIndex, ProjectIndexEntry
from services.project_factory.artifacts import write_archive_index, _resolve_project_factory_root
from services.project_factory.portfolio_metrics import generate_portfolio_metrics

def test_portfolio_metrics(tmp_path):
    root = _resolve_project_factory_root(str(tmp_path))
    root.mkdir(parents=True, exist_ok=True)
    
    archive = ArchiveIndex(
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_projects=3,
        closed_projects=1,
        active_projects=1,
        blocked_projects=1,
        revision_requested=0,
        projects=[
            ProjectIndexEntry(
                project_id="PF-1",
                title="P1",
                status="PROJECT_CLOSED",
                risk_level="LOW",
                quality_score=90,
                risk_score=10,
                release_id="REL-1",
                detail_url="/p1",
                created_at="time",
                updated_at="time"
            ),
            ProjectIndexEntry(
                project_id="PF-2",
                title="P2",
                status="PR_CREATION_BLOCKED",
                risk_level="HIGH",
                quality_score=50,
                risk_score=90,
                detail_url="/p2",
                created_at="time",
                updated_at="time"
            ),
            ProjectIndexEntry(
                project_id="PF-3",
                title="P3",
                status="HUMAN_GATE_WAITING",
                risk_level="LOW",
                quality_score=100,
                risk_score=5,
                detail_url="/p3",
                created_at="time",
                updated_at="time"
            )
        ]
    )
    
    write_archive_index(archive.model_dump(), str(tmp_path))
    
    metrics = generate_portfolio_metrics(str(tmp_path))
    
    assert metrics.total_projects == 3
    assert metrics.by_status["PROJECT_CLOSED"] == 1
    assert metrics.by_status["PR_CREATION_BLOCKED"] == 1
    assert metrics.by_status["HUMAN_GATE_WAITING"] == 1
    
    assert metrics.by_risk_level["LOW"] == 2
    assert metrics.by_risk_level["HIGH"] == 1
    
    assert metrics.average_quality_score == 80.0  # (90+50+100)/3
    assert metrics.average_risk_score == 35.0  # (10+90+5)/3
    
    assert metrics.release_archive_count == 1
    assert metrics.open_human_gates == 1
    assert metrics.blocked_count == 1
