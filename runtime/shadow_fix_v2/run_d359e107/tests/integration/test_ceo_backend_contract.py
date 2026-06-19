import uuid

import pytest
from sqlalchemy import delete, select

from libs.db.models import CEOSuggestedTask, LLMCostLog, Project, SovereignGoal
from libs.db.repositories.repository import CostRepository
from libs.db.session import session_scope
from services.orchestration.ceo.engine import CEOEngine
from services.orchestration.ceo.resource_governor import ResourceGovernor
from services.orchestration.ceo.strategy_motor import CEOStrategyMotor


class _FakeGoalResponse:
    content = """
    {
        "title": "CEO Contract Test Goal",
        "description": "Keep CEO strategy persistence schema-compatible.",
        "priority": "P1",
        "kpis": {"latency_target": 250}
    }
    """


class _BadGoalResponse:
    content = "not json"


class _FakeOrchestrator:
    def __init__(self, response):
        self._response = response

    async def complete_task(self, **kwargs):
        return self._response


@pytest.mark.asyncio
async def test_ceo_overview_serializes_suggested_tasks_with_current_model_fields():
    title = f"CEO overview contract {uuid.uuid4()}"
    async with session_scope() as db:
        suggestion = CEOSuggestedTask(
            title=title,
            description="Contract coverage for overview payload.",
            status="suggested",
            reasoning_summary="Schema-aligned reasoning.",
            impact_projection={"risk_reduction_pct": 25},
        )
        db.add(suggestion)
        await db.commit()

    try:
        overview = await CEOEngine(model_orch=None).get_overview()
        match = next(item for item in overview["suggestions"] if item["title"] == title)

        assert match["reasoning"] == "Schema-aligned reasoning."
        assert match["impact"] == {"risk_reduction_pct": 25}
    finally:
        async with session_scope() as db:
            await db.execute(delete(CEOSuggestedTask).where(CEOSuggestedTask.title == title))
            await db.commit()


@pytest.mark.asyncio
async def test_resource_governor_uses_repository_metrics_and_project_costs():
    project_id = uuid.uuid4()
    async with session_scope() as db:
        project = Project(id=project_id, title="CEO quota contract")
        db.add(project)
        await CostRepository.write(
            db,
            provider="test",
            model="contract",
            agent_id="ceo_contract",
            input_tokens=10,
            output_tokens=5,
            cost_usd=2.5,
            latency_s=0.1,
            project_id=project_id,
        )
        await db.commit()

    try:
        score = await ResourceGovernor.get_system_health_score()
        assert 0 <= score <= 100
        assert await ResourceGovernor.enforce_quota(str(project_id), 3.0) is True
        assert await ResourceGovernor.enforce_quota(str(project_id), 2.0) is False
    finally:
        async with session_scope() as db:
            await db.execute(delete(LLMCostLog).where(LLMCostLog.project_id == project_id))
            await db.execute(delete(Project).where(Project.id == project_id))
            await db.commit()


@pytest.mark.asyncio
async def test_strategy_motor_persists_schema_compatible_goal_and_skips_bad_json():
    motor = CEOStrategyMotor(_FakeOrchestrator(_FakeGoalResponse()))
    goals = await motor.formulate_new_goals([{"title": "contract finding"}])

    try:
        assert len(goals) == 1
        goal_id = goals[0].id

        async with session_scope() as db:
            result = await db.execute(select(SovereignGoal).where(SovereignGoal.id == goal_id))
            saved = result.scalar_one()

        assert saved.title == "CEO Contract Test Goal"
        assert saved.vision_statement == "Keep CEO strategy persistence schema-compatible."
        assert saved.priority == 80
        assert saved.kpis == {"latency_target": 250}

        bad_motor = CEOStrategyMotor(_FakeOrchestrator(_BadGoalResponse()))
        assert await bad_motor.formulate_new_goals([{"title": "bad finding"}]) == []
    finally:
        async with session_scope() as db:
            await db.execute(delete(SovereignGoal).where(SovereignGoal.title == "CEO Contract Test Goal"))
            await db.commit()
