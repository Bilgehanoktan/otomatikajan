
import asyncio
import uuid
from libs.workflow.engine import WorkflowEngine
from libs.workflow.models import WorkflowInstance, WorkflowStep, StepStatus
from libs.workflow.persistence import WorkflowPersistence

async def test_security_failure_persistence():
    from services.orchestration.agi.cognitive.cognitive_blackboard import get_blackboard
    from services.orchestration.agi.operational.tool_grounder import get_grounded_tool_input
    
    engine = WorkflowEngine()
    
    workflow_id = str(uuid.uuid4())
    
    # 1. Setup Blackboard with Security Warning
    bb = get_blackboard(workflow_id)
    await bb.post_warning("security_auditor", "Yasaklı yol tespiti: /etc/shadow erişimi kesinlikle kısıtlanmıştır.", severity="critical")
    
    # 2. Insert records into DB (since persistence expects them to exist)
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import Project, SubTask, ProjectStatus
    async with AsyncSessionLocal() as db:
        new_project = Project(
            id=uuid.UUID(workflow_id),
            title=f"Security Test {workflow_id[:8]}",
            workflow_template="security_test",
            status=ProjectStatus.RUNNING,
            execution_context={}
        )
        db.add(new_project)
        
        step_id = str(uuid.uuid4())
        new_subtask = SubTask(
            id=uuid.UUID(step_id),
            project_id=new_project.id,
            agent_id="Attempt Illegal Access",
            action="read_file",
            prompt="Attempting to read restricted file.",
            input_data={"path": "/etc/shadow"},
            status=ProjectStatus.PENDING
        )
        db.add(new_subtask)
        await db.commit()

    # 3. Define a malicious action that uses Grounding
    async def malicious_read_file(context, path):
        # In a real agent, this call is made before tool execution
        grounded_input = await get_grounded_tool_input(workflow_id, "read_file", {"path": path})
        if grounded_input == "BLOCKED_PATH_ACCESS":
            raise PermissionError(f"[GROUNDER] Security violation: Access to {path} is forbidden.")
        return {"data": "file content"}

    engine._registry["read_file"] = malicious_read_file
    
    # Define a step that triggers Grounder
    step = WorkflowStep(
        id=step_id,
        name="Attempt Illegal Access",
        action="read_file",
        input_data={"path": "/etc/shadow"},
        max_retries=0 # Don't retry for this test
    )
    
    instance = WorkflowInstance(
        id=workflow_id,
        workflow_type="security_test",
        steps=[step],
        context={}
    )
    
    print(f"Starting security test workflow: {workflow_id}")
    
    try:
        await engine.execute(instance)
    except Exception as e:
        print(f"Workflow execution caught: {e}")
        
    # Now check the persistence
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import SubTask, Project
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        # Check Project (WorkflowInstance)
        res_p = await db.execute(select(Project).where(Project.id == uuid.UUID(instance.id)))
        proj = res_p.scalar_one_or_none()
        print(f"--- RESULTS ---")
        print(f"Project ID: {instance.id}")
        print(f"Project Status: {proj.status if proj else 'NOT FOUND'}")
        print(f"Project Error Detail: {proj.error_detail if proj else 'N/A'}")
        
        # Check SubTask (WorkflowStep)
        res_s = await db.execute(select(SubTask).where(SubTask.project_id == uuid.UUID(instance.id)))
        st = res_s.scalar_one_or_none()
        print(f"SubTask Status: {st.status if st else 'NOT FOUND'}")
        print(f"SubTask Result: {st.result if st else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(test_security_failure_persistence())
