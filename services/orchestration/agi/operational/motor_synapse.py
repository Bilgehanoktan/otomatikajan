"""
Motor Synapse (Phase 20) — High-Velocity Motor Subsystem.
(Formerly Action Cortex)
Decision Matrix tarafından kararlaştırılan 'ExecutionPlan'ı motor impulslarına dönüştürür.
"""

import asyncio
import time
import uuid
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from services.observability.logging import get_logger
from services.orchestration.agi.schemas import ExecutionPlan, PlanStep, ActionRecord, RiskLevel
from services.orchestration.application.sandbox_runner import get_sandbox_runner
from libs.db.repositories.repository import SkillLogRepository
from libs.db.session import session_scope
# Faz 12.1 Stability: Event-Driven UI Updates
from services.orchestration.domain.events import event_bus
from libs.contracts.events import EVENT_SKILL_TRACE

_log = get_logger("agi_motor_synapse")

class MotorSynapse:
    """
    Operasyonel Çekirdek - Motor Sinapsı.
    Sistemin dış dünya ile etkileşime geçtiği 'kas' grubudur. 
    Yüksek hızlı motor impulsları (actions) üretir.
    """
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.sandbox = get_sandbox_runner()
        self.action_history: List[ActionRecord] = []

    async def execute_plan(self, plan: ExecutionPlan) -> List[ActionRecord]:
        """Verilen planı eyleme dök ve sonuçları ActionRecord olarak döndür."""
        _log.info(f"Motor döngüsü başlatıldı: {plan.plan_id} (Hedef: {plan.goal})")
        
        # Swarm Evolution (Phase 25): Paylaşımlı Çalışma Alanı
        workspace = getattr(plan, "workspace", {}).copy()
        
        step_events = {s.step_id: asyncio.Event() for s in plan.steps}
        results: List[ActionRecord] = []
        workspace_lock = asyncio.Lock()

        async def _run_step(step: PlanStep):
            for dep_id in step.dependencies:
                if dep_id in step_events:
                    await step_events[dep_id].wait()
            
            _log.debug(f"Motor impulsu gönderiliyor: {step.step_id} ({step.agent_id})")
            
            # Swarm Evolution (Phase 25) - Context Birleştirme
            async with workspace_lock:
                step_params = {**step.params, **workspace}
            
            record = await self._execute_motor_step(step, plan.plan_id, step_params)
            
            # Workspace Güncelleme (Basitleştirilmiş: Her agent'ın çıktısı workspace'e 'agent_id_output' olarak eklenir)
            async with workspace_lock:
                workspace[f"{step.agent_id}_output"] = record.output_data
                if record.workspace_update:
                    workspace.update(record.workspace_update)

            results.append(record)
            step_events[step.step_id].set()

        if not plan.steps:
            return []
            
        await asyncio.gather(*[_run_step(s) for s in plan.steps])
        
        _log.info(f"Motor döngüsü tamamlandı: {len(results)} impuls işlendi.")
        self.action_history.extend(results)
        return results

    async def _execute_motor_step(self, step: PlanStep, plan_id: str, dynamic_params: Optional[Dict] = None) -> ActionRecord:
        t_start = time.time()
        effective_params = dynamic_params or step.params
        max_retries = 2
        current_retry = 0
        last_error = ""
        
        record = ActionRecord(
            plan_id=plan_id,
            step_id=step.step_id,
            tool_used=step.agent_id,
            input_data=effective_params,
            timestamp=datetime.now(timezone.utc)
        )

        while current_retry <= max_retries:
            try:
                # Dinamik Araç Kontrolü (Neural Tool Weaver)
                from services.orchestration.agi.operational.neural_tool_weaver import tool_registry
                dynamic_tool = tool_registry.get_tool(step.agent_id)
                
                if dynamic_tool:
                    _log.info(f"Dinamik motor eklentisi (Synapse Plugin): {step.agent_id}")
                    with open(dynamic_tool["path"], "r", encoding="utf-8") as f:
                        code = f.read()
                    
                    wrapper = f"""
{code}
import json
try:
    res = main({json.dumps(effective_params)})
    print("---RESULT_START---")
    print(json.dumps(res))
    print("---RESULT_END---")
except Exception as e:
    print(f"ERROR: {{e}}")
    import sys
    sys.exit(1)
"""
                    res = await self.sandbox.run_python(wrapper)
                    if res.success:
                        import re
                        match = re.search(r"---RESULT_START---\n(.*?)\n---RESULT_END---", res.stdout, re.DOTALL)
                        record.output_data = json.loads(match.group(1)) if match else res.stdout
                        record.success = True
                        break
                    else:
                        raise Exception(res.stderr or "Unknown motor/synapse error")

                else:
                    agent = self.agents.get(step.agent_id)
                    if not agent:
                        from services.orchestration.agi.operational.neural_tool_weaver import neural_tool_weaver
                        weave_res = await neural_tool_weaver.weave_capability(f"Yeni motor gereksinimi: {step.agent_id}", step.agent_id)
                        if weave_res["status"] == "success":
                            from agents.specialist_agents.agent_registry import build_agents
                            self.agents = build_agents()
                            agent = self.agents.get(step.agent_id)
                        
                        if not agent:
                            raise ValueError(f"Motor unit failed to synthesize: {step.agent_id}")

                    result = await agent.execute(
                        task_id=plan_id,
                        subtask_id=step.step_id,
                        context=effective_params
                    )
                    record.output_data = result.raw_output
                    record.success = True
                    break

            except Exception as e:
                last_error = str(e)
                current_retry += 1
                if current_retry > max_retries:
                    record.success = False
                    record.errors.append(last_error)
                    break
        
        record.duration_s = time.time() - t_start
        
        # Bilişsel Loglama/İzlenebilirlik
        asyncio.create_task(self._persist_log(plan_id, step, record))
        return record

    async def _persist_log(self, plan_id: str, step: PlanStep, record: ActionRecord):
        try:
            try:
                p_id = uuid.UUID(plan_id)
            except ValueError: return
            
            async with session_scope() as db:
                await SkillLogRepository.write(
                    db, project_id=p_id, skill_id=step.agent_id,
                    agent_id=step.agent_id, success=record.success,
                    summary=f"{step.agent_id} executed via Motor Synapse",
                    data={"input": record.input_data, "output": record.output_data, "errors": record.errors},
                    duration_s=record.duration_s
                )
            await event_bus.emit(EVENT_SKILL_TRACE, {
                "job_id": str(p_id), "skill_id": step.agent_id,
                "success": record.success, "summary": f"Motor Synapse Pulse: {step.agent_id}",
                "duration_s": round(record.duration_s, 3)
            })
        except Exception as e:
            _log.warning(f"Motor synapse log persistence failed: {e}")

# singleton or separate init depending on architecture
