
import asyncio
import uuid
import sys
import os

# Add root to sys.path
sys.path.append(os.getcwd())

from libs.workflow.models import WorkflowInstance, WorkflowStep, WorkflowStatus
from libs.workflow.engine import WorkflowEngine
from libs.db.models.core_models import Project, SubTask, ProjectStatus
from libs.db.session import AsyncSessionLocal

async def run_smoke_test():
    workflow_id = str(uuid.uuid4())
    print(f"Starting smoke test workflow: {workflow_id}")

    # 1. Pre-insert project and subtask (persistence requirement)
    async with AsyncSessionLocal() as db:
        new_project = Project(
            id=uuid.UUID(workflow_id),
            title=f"Smoke Test {workflow_id[:8]}",
            description="A simple, non-malicious task to verify system health.",
            status=ProjectStatus.RUNNING,
            execution_context={}
        )
        db.add(new_project)
        
        step_id = str(uuid.uuid4())
        new_subtask = SubTask(
            id=uuid.UUID(step_id),
            project_id=new_project.id,
            agent_id="HealthCheckAgent",
            action="echo",
            prompt="Verification step.",
            input_data={"message": "System is stable."},
            status=ProjectStatus.PENDING
        )
        db.add(new_subtask)
        await db.commit()

    # 2. Setup engine
    engine = WorkflowEngine()
    
    # Mock action
    async def echo_action(context, message):
        return {"response": f"REPLY: {message}"}
    
    engine._registry["echo"] = echo_action

    # 3. Create instance
    step = WorkflowStep(
        id=step_id,
        name="Health Check",
        action="echo",
        input_data={"message": "System is stable."}
    )
    instance = WorkflowInstance(
        id=workflow_id,
        workflow_type="smoke_test",
        steps=[step]
    )

    # 4. Execute
    print("Executing workflow...")
    await engine.execute(instance)

    # 5. Verify persistence
    print("\n--- SMOKE TEST RESULTS ---")
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        res_p = await db.execute(select(Project).where(Project.id == uuid.UUID(workflow_id)))
        project = res_p.scalar_one_or_none()
        
        res_s = await db.execute(select(SubTask).where(SubTask.project_id == uuid.UUID(workflow_id)))
        subtask = res_s.scalar_one_or_none()
        
        print(f"Project Status: {project.status}")
        print(f"SubTask Status: {subtask.status}")
        print(f"SubTask Result: {subtask.result}")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
