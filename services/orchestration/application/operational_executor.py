import asyncio
import time
from datetime import datetime, timezone
from sqlalchemy import update
from typing import Any, Dict, List, Optional
from services.observability.logging import get_logger
from services.orchestration.domain.models import ProjectTask, TaskStatus, SubTask
from services.orchestration.application.velocity_engine import velocity_engine
from services.orchestration.application.metabolic_governor import metabolic_governor
from services.repair.application.heal_engine import heal_engine # Autonomous Healing
from libs.db.models.core_models import SubTask as DbSubTask

_log = get_logger("agi_operational_executor")

class OperationalExecutor:
    def __init__(self, model_orch, affective_core, reflective_synthesizer=None):
        self.model_orch = model_orch
        self.affective = affective_core
        self.reflection = reflective_synthesizer

    async def execute_task_tree(self, task: ProjectTask):
        events = {st.id: asyncio.Event() for st in task.subtasks}
        await asyncio.gather(*[self._process_node_recursive(st, task, events) for st in task.subtasks])

    async def _process_node_recursive(self, st: SubTask, task: ProjectTask, events: Dict[str, asyncio.Event], depth: int = 0):
        dependencies = getattr(st, "dependencies", [])
        for dep_id in dependencies:
            if dep_id in events: 
                await events[dep_id].wait()
        
        if st.status == TaskStatus.COMPLETED:
            events[st.id].set()
            return

        max_depth = 3
        if getattr(st, "is_complex", False) and depth < max_depth:
            m_safety = metabolic_governor.check_safety()
            if m_safety["can_expand"]:
                # Recursive expansion logic...
                _log.info(f"[EXECUTOR] Expanding complex task: {st.id}")
                pass

        await self._execute_subtask_nexus(task, st)
        events[st.id].set()

    async def _execute_subtask_nexus(self, task: ProjectTask, subtask: SubTask):
        from services.orchestration.agi.cognitive.cognitive_blackboard import get_blackboard
        from services.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
        from libs.memory.retrieval import context_builder
        from libs.db.session import AsyncSessionLocal
        from services.orchestration.agi.schemas import ProblemFrame, TaskType, RiskLevel
        from libs.db.repositories.repository import SubTaskRepository

        try:
            async with AsyncSessionLocal() as db_mem:
                past_lessons = await synaptic_cortex.search_with_causal_anchoring(db=db_mem, query=f"{subtask.title} {subtask.prompt}", top_k=5, use_synergy=True)
                if past_lessons:
                    lesson_strings = []
                    for m in past_lessons:
                        if isinstance(m, dict):
                            body = m.get('body', "")
                        else:
                            body = getattr(m, 'body', str(m))
                        lesson_strings.append(f"- {body}")
                    subtask.prompt += "\n\n### 🧠 BİLİŞSEL MİRAS:\n" + "\n".join(lesson_strings)
            
            subtask.status = TaskStatus.RUNNING
            t_start = time.time()
            enriched_context = await context_builder.build_context(agent_id=subtask.agent_id, task_text=subtask.prompt, project_id=task.id)
            context_dict = {"working_context": enriched_context}
            if task.execution_context and "shared_state" in task.execution_context:
                context_dict["shared_state"] = task.execution_context["shared_state"]
            
            # Faz 8: Persistent START status
            async with AsyncSessionLocal() as db_sync:
                await db_sync.execute(
                    update(DbSubTask)
                    .where(DbSubTask.id == subtask.id)
                    .values(status=TaskStatus.RUNNING, updated_at=datetime.now(timezone.utc))
                )
                await db_sync.commit()

            result = await velocity_engine.simulate_and_execute(agent_id=subtask.agent_id, prompt=subtask.prompt, context=context_dict, task_id=task.id)
            
            if result.success:
                subtask.status = TaskStatus.COMPLETED
                subtask.result = str(result.output_data)
                
                # [Phase 36: Cognitive Continuity] Extract and update shared state
                if "[STATE_UPDATE]" in subtask.result:
                    try:
                        import re
                        state_match = re.search(r'\[STATE_UPDATE\]\s*(\{.*?\})', subtask.result, re.DOTALL)
                        if state_match:
                            import json
                            updates = json.loads(state_match.group(1))
                            if "shared_state" not in task.execution_context:
                                task.execution_context["shared_state"] = {}
                            task.execution_context["shared_state"].update(updates)
                            _log.info(f"[EXECUTOR-STATE] Shared state updated successfully: {task.execution_context['shared_state']}")
                    except Exception as se_err:
                        _log.error(f"[EXECUTOR-STATE] Failed to parse state update: {se_err}")
                subtask.internal_monologue = result.reflection
                subtask.quality_score = result.quality_score
                subtask.quality_detail = result.quality_detail
                
                # Faz 12.3: Bilişsel Yansıtma Denetimi (Reflective Audit)
                if self.reflection:
                    _log.info(f"[EXECUTOR] Sonuç denetleniyor (Reflection Audit): {subtask.agent_id}")
                    frame = ProblemFrame(task_type=TaskType.OPERATION, objective=subtask.title, risk_level=RiskLevel.MEDIUM)
                    audit_result = await self.reflection.audit_subtask(subtask, frame, context=enriched_context)
                    
                    if not audit_result.get("is_valid", True):
                        _log.warning(f"[EXECUTOR-AUDIT] Denetim BAŞARISIZ: {audit_result.get('critique')}")
                        raise Exception(f"Bilişsel Denetim Reddi: {audit_result.get('critique')}")
                    
                    subtask.causal_anchor = audit_result.get('causal_anchor', "")
                    # Reflection can also adjust quality score
                    if audit_result.get("quality_score"):
                        subtask.quality_score = audit_result["quality_score"]
                    _log.info(f"[EXECUTOR-AUDIT] Denetim onaylandı. Anchor: {subtask.causal_anchor}")

                # Otonom Başarı Sinyali
                heal_engine.on_subtask_success(subtask.agent_id, time.time() - t_start)
            else:
                raise Exception(f"Agent {subtask.agent_id} reported failure in output.")
            
            subtask.duration_s = time.time() - t_start

            # Faz 8: Persistent COMPLETE status + Metrics
            async with AsyncSessionLocal() as db_sync:
                await SubTaskRepository.mark_completed(
                    db=db_sync,
                    subtask_id=subtask.id,
                    result=subtask.result,
                    provider="velocity_engine",
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0.0,
                    latency_s=subtask.duration_s,
                    quality_score=subtask.quality_score,
                    quality_detail=subtask.quality_detail,
                    internal_monologue=subtask.internal_monologue,
                    causal_anchor=getattr(subtask, "causal_anchor", "")
                )
                await db_sync.commit()
        except Exception as e:
            _log.error(f"[EXECUTOR] Subtask nexus failed: {e}")
            subtask.status = TaskStatus.ERROR
            subtask.result = str(e)
            
            # Otonom Öz-İyileştirme (Self-Healing) Döngüsü
            await heal_engine.on_subtask_error(subtask.agent_id, str(e))
            
            _log.info(f"[EXECUTOR-HEAL] Hata saptandı, otonom onarım denemesi başlatılıyor: {subtask.agent_id}")
            recovered = await heal_engine.recover_subtask(subtask.agent_id, subtask)
            
            if recovered:
                _log.info(f"[EXECUTOR-HEAL] OTONOM ONARIM BAŞARILI: {subtask.agent_id}")
                subtask.status = TaskStatus.COMPLETED
                
                # Faz 8: Persistent HEALED status
                async with AsyncSessionLocal() as db_sync:
                    await SubTaskRepository.mark_completed(
                        db=db_sync,
                        subtask_id=subtask.id,
                        result=subtask.result,
                        recovered=True,
                        latency_s=subtask.duration_s,
                        internal_monologue=f"[HEALED] {subtask.internal_monologue}"
                    )
                    await db_sync.commit()
            else:
                _log.warning(f"[EXECUTOR-HEAL] Onarım başarısız veya strateji bulunamadı.")
                # Faz 8: Persistent FAIL status
                async with AsyncSessionLocal() as db_sync:
                    await SubTaskRepository.mark_failed(
                        db=db_sync,
                        subtask_id=subtask.id,
                        result=str(e),
                        attempts=subtask.attempts,
                        internal_monologue=getattr(subtask, "internal_monologue", "")
                    )
                    await db_sync.commit()
