import pytest

from libs.workflow.engine import WorkflowEngine
from libs.workflow.models import WorkflowInstance, WorkflowStatus, WorkflowStep


class InMemoryPersistence:
    def __init__(self, instance):
        self.instance = instance
        self.events = []

    async def save_instance(self, instance):
        self.instance = instance

    async def save_step(self, instance_id, step):
        return None

    async def save_event(self, project_id, event_type, step_id=None, payload=None):
        self.events.append(event_type)

    async def load_instance(self, project_id):
        return self.instance

    async def load_history(self, project_id):
        return []


@pytest.mark.asyncio
async def test_engine_fails_when_semantic_final_status_is_error():
    engine = WorkflowEngine()
    step = WorkflowStep(id="report", name="report", action="report")
    instance = WorkflowInstance(id="wf-semantic-error", workflow_type="test", steps=[step])
    engine.persistence = InMemoryPersistence(instance)

    async def report(context, **kwargs):
        return {"_context_update": {"final_status": "TaskStatus.ERROR"}}

    engine.register_action("report", report)

    await engine.execute(instance)

    assert instance.status == WorkflowStatus.FAILED
    assert "semantic final status" in (instance.error or "")
