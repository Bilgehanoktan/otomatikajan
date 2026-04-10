import asyncio
import time
from typing import Any, Dict, List, Optional
from packages.observability.logging import get_logger
from packages.orchestration.domain.models import ProjectTask, TaskStatus, SubTask
from packages.orchestration.application.velocity_engine import velocity_engine
from packages.orchestration.application.metabolic_governor import metabolic_governor
from packages.healing.application.heal_engine import heal_engine # Autonomous Healing

_log = get_logger("agi_operational_executor")

class OperationalExecutor:
    def __init__(self, model_orch, affective_core):
        self.model_orch = model_orch
        self.affective = affective_core

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
                # (Logic from SovereignCortex _process_node_recursive)
                pass

        await self._execute_subtask_nexus(task, st)
        events[st.id].set()

    async def _execute_subtask_nexus(self, task: ProjectTask, subtask: SubTask):
        from packages.orchestration.agi.cognitive.cognitive_blackboard import get_blackboard
        from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
        from packages.memory.retrieval import context_builder
        from packages.persistence.session import AsyncSessionLocal

        try:
            async with AsyncSessionLocal() as db_mem:
                past_lessons = await synaptic_cortex.search_with_causal_anchoring(db=db_mem, query=f"{subtask.title} {subtask.prompt}", top_k=5, use_synergy=True)
                if past_lessons:
                    subtask.prompt += "\n\n### 🧠 BİLİŞSEL MİRAS:\n" + "\n".join([f"- {m.get('body')}" for m in past_lessons])
            
            subtask.status = TaskStatus.RUNNING
            t_start = time.time()
            enriched_context = await context_builder.build_context(agent_id=subtask.agent_id, task_text=subtask.prompt, project_id=task.id)
            result = await velocity_engine.simulate_and_execute(agent_id=subtask.agent_id, prompt=subtask.prompt, context=enriched_context, task_id=task.id)
            
            if result.success:
                subtask.status = TaskStatus.COMPLETED
                subtask.result = str(result.output_data)
                # Otonom Başarı Sinyali
                heal_engine.on_subtask_success(subtask.agent_id, time.time() - t_start)
            else:
                # Re-throw for exception handler if result failed but didn't exception
                raise Exception(f"Agent {subtask.agent_id} reported failure in output.")
            
            subtask.duration_s = time.time() - t_start
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
            else:
                _log.warning(f"[EXECUTOR-HEAL] Onarım başarısız veya strateji bulunamadı.")
