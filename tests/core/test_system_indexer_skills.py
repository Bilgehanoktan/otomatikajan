import json
from pathlib import Path

from core.system_indexer import SystemIndexer


def _write_index(index_path: Path, payload: dict):
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_search_by_symbol_exact_match(tmp_path: Path):
    root = tmp_path
    index_path = root / "workspace" / "code_index.json"

    payload = {
        "entries": [
            {
                "path": "skills/router.py",
                "summary": "router file",
                "symbols": ["SkillRouter", "TaskRouter"],
                "imports": ["skills.registry"],
            }
        ]
    }
    _write_index(index_path, payload)

    indexer = SystemIndexer(project_root=str(root))
    result = indexer.search_by_symbol("SkillRouter")

    assert len(result) == 1
    assert result[0]["path"] == "skills/router.py"


def test_search_by_symbol_case_insensitive(tmp_path: Path):
    root = tmp_path
    index_path = root / "workspace" / "code_index.json"

    payload = {
        "entries": [
            {
                "path": "skills/router.py",
                "summary": "router file",
                "symbols": ["SkillRouter"],
                "imports": [],
            }
        ]
    }
    _write_index(index_path, payload)

    indexer = SystemIndexer(project_root=str(root))
    result = indexer.search_by_symbol("skillrouter")

    assert len(result) == 1
    assert result[0]["path"] == "skills/router.py"


def test_impact_analysis_returns_empty_when_no_primary_hit(tmp_path: Path, monkeypatch):
    root = tmp_path
    indexer = SystemIndexer(project_root=str(root))

    monkeypatch.setattr(indexer, "search", lambda query, limit=8: [])
    monkeypatch.setattr(indexer, "read_index", lambda: {"entries": []})

    result = indexer.impact_analysis("does-not-exist")

    assert result == []


def test_impact_analysis_returns_related_candidates(tmp_path: Path, monkeypatch):
    root = tmp_path
    indexer = SystemIndexer(project_root=str(root))

    entries = [
        {
            "path": "core/orchestrator.py",
            "summary": "orchestrator uses SkillRouter and task flow",
            "symbols": ["Orchestrator"],
            "imports": ["skills.router"],
        },
        {
            "path": "skills/router.py",
            "summary": "router file",
            "symbols": ["SkillRouter"],
            "imports": ["skills.registry"],
        },
        {
            "path": "api/task_write_router.py",
            "summary": "task write calls orchestrator",
            "symbols": ["create_task"],
            "imports": ["skills.router"],
        },
    ]

    monkeypatch.setattr(indexer, "read_index", lambda: {"entries": entries})
    monkeypatch.setattr(indexer, "search", lambda query, limit=8: [entries[0]])

    result = indexer.impact_analysis("orchestrator")

    paths = [r["path"] for r in result]
    assert "core/orchestrator.py" not in paths
    assert "skills/router.py" in paths or "api/task_write_router.py" in paths
