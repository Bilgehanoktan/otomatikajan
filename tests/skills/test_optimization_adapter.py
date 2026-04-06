import pytest

from packages.skills.base import SkillRequest
from packages.skills.adapters.optimization_adapter import OptimizationSkillAdapter


@pytest.mark.asyncio
async def test_optimization_adapter_trims_context():
    adapter = OptimizationSkillAdapter()

    req = SkillRequest(
        task_type="generic",
        title="A" * 300,
        description="B" * 5000,
        context={
            "memories": [f"m{i}" for i in range(20)],
            "file_hits": [f"f{i}" for i in range(20)],
            "shared_context": "C" * 10000,
        },
    )

    result = await adapter.execute(req)

    assert result.success is True
    assert result.skill_id == "optimization"
    assert len(result.data["title"]) <= 200
    assert len(result.data["description"]) <= 2000
    assert len(result.data["memories"]) == 5
    assert len(result.data["file_hits"]) == 5
    assert len(result.data["shared_context"]) <= 4000
    assert len(result.warnings) >= 1


@pytest.mark.asyncio
async def test_optimization_adapter_handles_empty_context():
    adapter = OptimizationSkillAdapter()

    req = SkillRequest(
        task_type="generic",
        title="optimize prompt",
        description="short",
        context={},
    )

    result = await adapter.execute(req)

    assert result.success is True
    assert result.data["memories"] == []
    assert result.data["file_hits"] == []
    assert result.data["shared_context"] == ""
