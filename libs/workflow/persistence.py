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
                existing.action = step.action
                existing.dependencies = step.dependencies
                existing.input_data = step.input_data
                existing.input_schema = step.input_schema
                
                # Faz 8 Integration: Capture reasoning and metrics
                if step.output_data and isinstance(step.output_data, dict):
                    existing.internal_monologue = step.output_data.get("internal_monologue", existing.internal_monologue)
                    existing.llm_provider = step.output_data.get("llm_provider", existing.llm_provider)
                    existing.input_tokens = step.output_data.get("input_tokens", existing.input_tokens)
                    existing.output_tokens = step.output_data.get("output_tokens", existing.output_tokens)
                    existing.cost_usd = step.output_data.get("cost_usd", existing.cost_usd)
                    existing.latency_s = step.output_data.get("latency_s", existing.latency_s)
                    existing.quality_score = step.output_data.get("quality_score", existing.quality_score)
            else:
                new_subtask = SubTask(
                    id=UUID(step.id),
                    project_id=UUID(instance_id),
                    agent_id=step.name,
                    action=step.action,
                    prompt=step.input_data.get("prompt", ""),
                    input_data=step.input_data,
                    input_schema=step.input_schema,
                    status=step.status.value,
                    attempts=step.retries,
                    dependencies=step.dependencies,
                    internal_monologue=step.output_data.get("internal_monologue", "") if step.output_data else ""
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
                    action=st.action,
                    input_data=st.input_data if st.input_data else {"prompt": st.prompt},
                    input_schema=st.input_schema or {},
                    output_data={"result": st.result} if st.result else None,
                    status=StepStatus(st.status.lower()),
                    retries=st.attempts,
                    dependencies=st.dependencies or []
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
    async def save_event(
        project_id: Optional[str], 
        event_type: str, 
        step_id: Optional[str] = None, 
        payload: Optional[dict] = None,
        operator_id: str = "system"
    ):
        """
        Record a durable, tamper-evident workflow event.
        Faz 13.04: Chaining (Signatures) aktif edildi.
        If project_id is None, it records as a system-wide global event.
        """
        import hashlib
        import json
        from sqlalchemy import desc

        async with AsyncSessionLocal() as session:
            # 1. Chaining için bir önceki event'in imzasını bul (scope bazlı)
            stmt = (
                select(WorkflowEvent)
                .order_by(desc(WorkflowEvent.created_at))
                .limit(1)
            )
            if project_id:
                stmt = stmt.where(WorkflowEvent.project_id == UUID(project_id))
            else:
                stmt = stmt.where(WorkflowEvent.project_id == None)
                
            res = await session.execute(stmt)
            last_event = res.scalar_one_or_none()
            prev_hash = last_event.signature if last_event else "0" * 64

            # 2. Event oluştur
            event = WorkflowEvent(
                project_id=UUID(project_id) if project_id else None,
                event_type=event_type,
                step_id=step_id,
                operator_id=operator_id,
                payload=payload or {},
                previous_hash=prev_hash
            )

            # 3. İmzala (Tamper-Evidence)
            # Karma verisi: project + type + step + operator + payload + prev_hash
            canonical_payload = json.dumps(payload or {}, sort_keys=True)
            sign_text = f"{project_id}|{event_type}|{step_id or ''}|{operator_id}|{canonical_payload}|{prev_hash}"
            event.signature = hashlib.sha256(sign_text.encode()).hexdigest()

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
                    "operator_id": e.operator_id,
                    "step_id": e.step_id,
                    "payload": e.payload,
                    "signature": e.signature,
                    "previous_hash": e.previous_hash,
                    "created_at": e.created_at
                }
                for e in events
            ]
