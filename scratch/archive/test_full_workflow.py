
import asyncio
import sys
import os
import uuid
sys.path.append(os.getcwd())

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project
from libs.workflow.runner import run_project_workflow

async def test_fresh_workflow():
    p_id = str(uuid.uuid4())
    print(f"Creating test project: {p_id}")
    
    async with AsyncSessionLocal() as db:
        project = Project(
            id=p_id,
            title="System Stabilization Verification",
            description="Diagnostic task to verify that the AGI control plane is correctly executing workflows in Stable Degraded mode.",
            status="PENDING",
            review_required=False
        )
        db.add(project)
        await db.commit()
        
    print("Starting workflow execution...")
    try:
        instance = await run_project_workflow(
            project_id=p_id,
            title=project.title,
            description=project.description
        )
        print(f"Workflow finished with status: {instance.status}")
        print(f"Final Report Extract: {instance.context.get('final_report', 'No report')[:200]}...")
        
        if instance.status == "completed":
            print("PASS: System is executing workflows correctly.")
        else:
            print(f"FAIL: Workflow ended with {instance.status}")
            # Analyze steps
            for step in instance.steps:
                print(f"  Step {step.name}: {step.status} | Error: {step.error}")
    except Exception as e:
        print(f"CRITICAL ERROR during test: {e}")

if __name__ == "__main__":
    asyncio.run(test_fresh_workflow())
