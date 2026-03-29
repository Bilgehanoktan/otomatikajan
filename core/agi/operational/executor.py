import asyncio
import time
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from core.agi.schemas import ExecutionPlan, PlanStep, ActionRecord, RiskLevel
from core.sandbox_runner import get_sandbox_runner
from agents.agent_registry import build_agents

_log = get_logger("agi_executor")

class OperationalExecutor:
    """
    Operasyonel Çekirdek - Yürütme Katmanı.
    Karar almaz, sadece verilen 'ExecutionPlan'ı adım adım (DAG) uygular.
    """
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.sandbox = get_sandbox_runner()
        self.action_history: List[ActionRecord] = []

    async def execute_plan(self, plan: ExecutionPlan) -> List[ActionRecord]:
        _log.info(f"Yürütme başlatıldı: {plan.plan_id} (Hedef: {plan.goal})")
        
        # Olaylar (Events) aracılığıyla DAG bağımlılıklarını yönet
        step_events = {s.step_id: asyncio.Event() for s in plan.steps}
        results: List[ActionRecord] = []

        async def _run_step(step: PlanStep):
            # 1. Bağımlılıkları bekle
            for dep_id in step.dependencies:
                if dep_id in step_events:
                    await step_events[dep_id].wait()
            
            # 2. Adımı yürüt
            _log.debug(f"Adım yürütülüyor: {step.step_id} ({step.agent_id})")
            record = await self._execute_step(step, plan.plan_id)
            results.append(record)
            
            # 3. Adımı tamamla
            step_events[step.step_id].set()

        # 4. Tüm adımları paralel (bağımlılık sırasıyla) başlat
        await asyncio.gather(*[_run_step(s) for s in plan.steps])
        
        _log.info(f"Yürütme tamamlandı: {len(results)} adım işlendi.")
        self.action_history.extend(results)
        return results

    async def _execute_step(self, step: PlanStep, plan_id: str) -> ActionRecord:
        t_start = time.time()
        record = ActionRecord(
            plan_id=plan_id,
            step_id=step.step_id,
            tool_used=step.agent_id, # Agent is the primary 'tool' here
            input_data=step.params,
            timestamp=datetime.now(timezone.utc)
        )

        try:
            agent = self.agents.get(step.agent_id)
            if not agent:
                # Dinamik ajan yükleme logic'i (legacy or orchestrator logic) buraya eklenebilir
                raise ValueError(f"Agent not found: {step.agent_id}")

            # Execution context (Shared state and previous results)
            # Not: Operasyonel çekirdek karar almaz, ama parametreleri kullanır
            result = await agent.execute(
                task_id=plan_id,
                subtask_id=step.step_id,
                context=step.params
            )
            
            record.output_data = result.raw_output
            record.success = True
            
        except Exception as e:
            _log.error(f"Adım hatası ({step.step_id}): {e}")
            record.success = False
            record.errors.append(str(e))
        
        record.duration_s = time.time() - t_start
        return record

from datetime import datetime, timezone
