import pytest

from packages.packages.skills.base import SkillRequest
from packages.packages.skills.adapters.file_search_adapter import FileSearchSkillAdapter


class _FakeIndexer:
    def __init__(self, project_root=None, index_path="workspace/code_index.json"):
        self.project_root = project_root
        self.index_path = index_path

    def search(self, query: str, limit: int = 8):
        assert "orchestrator" in query.lower()
        return [
            {
                "path": "core/orchestrator.py",
                "summary": "orch",
                "symbols": ["Orchestrator"],
            }
        ]

    def impact_analysis(self, query: str, limit: int = 6):
        assert "orchestrator" in query.lower()
        return [
            {
                "path": "api/task_write_router.py",
                "summary": "task route",
            }
        ]


@pytest.mark.asyncio
async def test_file_search_adapter_returns_hits_and_impact(monkeypatch):
    monkeypatch.setattr(
        "core.system_indexer.SystemIndexer",
        _FakeIndexer,
    )

    adapter = FileSearchSkillAdapter()
    req = SkillRequest(
        task_type="generic",
        title="orchestrator impact",
        description="find dependency impact in orchestrator",
    )

    result = await adapter.execute(req)

    assert result.success is True
    assert result.skill_id == "file_search"
    assert len(result.data["hits"]) == 1
    assert len(result.data["impact_candidates"]) == 1
    assert result.data["hits"][0]["path"] == "core/orchestrator.py"
