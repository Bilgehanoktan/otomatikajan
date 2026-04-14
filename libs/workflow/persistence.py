from uuid import UUID
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, SubTask, ProjectStatus, WorkflowEvent
from libs.workflow.models import WorkflowInstance, WorkflowStep, StepStatus, WorkflowStatus

class WorkflowPersistence:
    @staticmethod
    async def save_instance(instance: WorkflowInstance):
        async with AsyncSessionLocal() as session:
            # Sync to Project table
            stmt = update(Project).where(Project.id == UUID(instance.id)).values(
                status=instance.status.value,
                execution_context=instance.context,
                started_at=instance.started_at,
                completed_at=instance.completed_at,
                updated_at=datetime.utcnow()
            )
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def save_step(instance_id: str, step: WorkflowStep):
        async with AsyncSessionLocal() as session:
            # Sync to SubTask table
            # Check if exists
            res = await session.execute(select(SubTask).where(SubTask.id == UUID(step.id)))
            existing = res.scalar_one_or_none()
            
            if existing:
                existing.status = step.status.value
                existing.result = str(step.output_data) if step.output_data else ""
                existing.attempts = step.retries
                existing.completed_at = step.completed_at
            else:
                new_subtask = SubTask(
                    id=UUID(step.id),
                    project_id=UUID(instance_id),
                    agent_id=step.name,
                    prompt=str(step.input_data),
                    status=step.status.value,
                    attempts=step.retries
                )
                session.add(new_subtask)
            
            await session.commit()

    @staticmethod
    async def load_instance(project_id: str) -> Optional[WorkflowInstance]:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(Project).where(Project.id == UUID(project_id))
            )
            project = res.scalar_one_or_none()
            if not project:
                return None
            
            # Load subtasks as steps
            res_steps = await session.execute(
                select(SubTask).where(SubTask.project_id == project.id).order_by(SubTask.created_at)
            )
            subtasks = res_steps.scalars().all()
            
            steps = []
            for st in subtasks:
                steps.append(WorkflowStep(
                    id=str(st.id),
                    name=st.agent_id,
                    action="run_agent", # default
                    input_data={"prompt": st.prompt},
                    output_data={"result": st.result} if st.result else None,
                    status=StepStatus(st.status.lower()),
                    retries=st.attempts
                ))
            
            return WorkflowInstance(
                id=str(project.id),
                workflow_type=project.workflow_template,
                status=WorkflowStatus(project.status.lower()),
                steps=steps,
                context=project.execution_context or {},
                created_at=project.created_at,
                review_required=project.review_required
            )

    @staticmethod
    async def save_event(project_id: str, event_type: str, step_id: Optional[str] = None, payload: Optional[dict] = None):
        """Record a durable workflow event."""
        async with AsyncSessionLocal() as session:
            event = WorkflowEvent(
                project_id=UUID(project_id),
                event_type=event_type,
                step_id=step_id,
                payload=payload or {}
            )
            session.add(event)
            await session.commit()

    @staticmethod
    async def load_history(project_id: str) -> List[dict]:
        """Load all events for a project, ordered by creation time."""
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                select(WorkflowEvent)
                .where(WorkflowEvent.project_id == UUID(project_id))
                .order_by(WorkflowEvent.created_at)
            )
            events = res.scalars().all()
            return [
                {
                    "event_type": e.event_type,
                    "step_id": e.step_id,
                    "payload": e.payload,
                    "created_at": e.created_at
                }
                for e in events
            ]
