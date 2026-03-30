from types import SimpleNamespace

import pytest

from memory.store import memory_store


@pytest.mark.asyncio
async def test_memory_write_gate_rejects_low_importance():
    allowed = await memory_store.memory_write_gate(
        db=None,
        data=SimpleNamespace(importance=0.1),
        category="episode_record",
    )
    assert allowed is False


@pytest.mark.asyncio
async def test_memory_write_gate_accepts_verified_episode_without_deletion_logic():
    verification = SimpleNamespace(result_status=True)
    data = SimpleNamespace(
        importance=0.9,
        verification=verification,
        problem_frame=SimpleNamespace(objective="Traceability", task_type=SimpleNamespace(value="analysis")),
        final_output="ok",
        lessons_learned=["kept previous memory"],
    )

    allowed = await memory_store.memory_write_gate(db=None, data=data, category="episode_record")

    assert allowed is True
