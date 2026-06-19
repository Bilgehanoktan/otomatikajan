import uuid

import pytest

from libs.db.models.core_models import ProjectStatus
from libs.db.repositories.repository import ProjectRepository


class _FakeAsyncSession:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)


@pytest.mark.asyncio
async def test_mark_completed_accepts_worker_quality_metadata():
    db = _FakeAsyncSession()

    await ProjectRepository.mark_completed(
        db,
        uuid.uuid4(),
        report="done",
        status=ProjectStatus.COMPLETED.value,
        quality_score=0.94,
        quality_detail={"source": "workflow_runner"},
    )

    assert len(db.statements) == 1
