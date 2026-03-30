import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from core.agi.schemas import ExecutionPlan, PlanStep, ActionRecord, RiskLevel
from core.sandbox_runner import get_sandbox_runner
from agents.agent_registry import build_agents
from db.repository import SkillLogRepository
from db.session import session_scope
from api.ws_manager import ws_manager

_log = get_logger("agi_motor_subsystem")

class MotorSubsystem:
    """
    Operasyonel Çekirdek - Motor Alt Sistemi (Motor Subsystem).
    Decision Matrix tarafından kararlaştırılan 'ExecutionPlan'ı adım adım (DAG) fiziksel/dijital eylemlere dönüştürür.
    Bu birim, sistemin dış dünya ile etkileşime geçtiği "kas" grubudur.
    """
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.sandbox = get_sandbox_runner()
        self.action_history: List[ActionRecord] = []

    async def execute_plan(self, plan: ExecutionPlan) -> List[ActionRecord]:
        """
        Verilen planı eyleme dök ve sonuçları ActionRecord olarak döndür.
        """
        _log.info(f"Eylem döngüsü başlatıldı: {plan.plan_id} (Hedef: {plan.goal})")
        
        # Olaylar (Events) aracılığıyla DAG bağımlılıklarını yönet
        step_events = {s.step_id: asyncio.Event() for s in plan.steps}
        results: List[ActionRecord] = []

        async def _run_step(step: PlanStep):
            # 1. Bağımlılıkları bekle
            for dep_id in step.dependencies:
                if dep_id in step_events:
                    await step_events[dep_id].wait()
            
            # 2. Adımı yürüt (Motor impulsu)
            _log.debug(f"Motor impulsu gönderiliyor: {step.step_id} ({step.agent_id})")
            record = await self._execute_motor_step(step, plan.plan_id)
            results.append(record)
            
            # 3. Adımı tamamla
            step_events[step.step_id].set()

        # 4. Tüm adımları paralel (bağımlılık sırasıyla) başlat
        await asyncio.gather(*[_run_step(s) for s in plan.steps])
        
        _log.info(f"Eylem döngüsü tamamlandı: {len(results)} adım işlendi.")
        self.action_history.extend(results)
        return results

    async def _execute_motor_step(self, step: PlanStep, plan_id: str) -> ActionRecord:
        t_start = time.time()
        # Yerel Hata Kurtarma Ayarları (Faz 13.4)
        max_retries = 2
        current_retry = 0
        last_error = ""
        
        record = ActionRecord(
            plan_id=plan_id,
            step_id=step.step_id,
            tool_used=step.agent_id,
            input_data=step.params,
            timestamp=datetime.now(timezone.utc)
        )

        while current_retry <= max_retries:
            if current_retry > 0:
                _log.info(f"Motor rejenerasyonu/Yeniden deneme: {step.step_id} (Deneme {current_retry}/{max_retries})")
                await asyncio.sleep(1.0 * current_retry) # Simple jitter/backoff
            
            try:
                # --- Dinamik Araç Kontrolü (Phase 12.4) ---
                from core.agi.operational.tool_weaver import tool_registry
                dynamic_tool = tool_registry.get_tool(step.agent_id)
                
                if dynamic_tool:
                    _log.info(f"Dinamik motor eklentisi çalıştırılıyor: {step.agent_id}")
                    with open(dynamic_tool["path"], "r", encoding="utf-8") as f:
                        code = f.read()
                    
                    import json
                    wrapper = f"""
{code}
import json
try:
    res = main({json.dumps(step.params)})
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
                        raise Exception(res.stderr or "Unknown motor/tool error")

                else:
                    # Normal Ajan Yürütme (Ajan bir motor ünitesi gibi davranır)
                    agent = self.agents.get(step.agent_id)
                    if not agent:
                        from core.agi.operational.tool_weaver import tool_weaver
                        weave_res = await tool_weaver.weave_capability(f"Yeni ajan/motor gereksinimi: {step.agent_id}", step.agent_id)
                        if weave_res["status"] == "success":
                            return await self._execute_motor_step(step, plan_id)
                        else:
                            raise ValueError(f"Motor unit (Agent) not found and synthesis failed: {step.agent_id}")

                    result = await agent.execute(
                        task_id=plan_id,
                        subtask_id=step.step_id,
                        context=step.params
                    )
                    record.output_data = result.raw_output
                    record.success = True
                    break

            except Exception as e:
                last_error = str(e)
                _log.error(f"Motor impulsu hatası ({step.step_id}, Deneme {current_retry}): {e}")
                current_retry += 1
                if current_retry > max_retries:
                    record.success = False
                    record.errors.append(last_error)
                    break
        
        record.duration_s = time.time() - t_start
        
        # --- Kalıcı Beceri Loglama (Async) ---
        async def _persist_motor_log():
            try:
                try:
                    p_id = uuid.UUID(plan_id)
                except ValueError:
                    return
                
                async with session_scope() as db:
                    await SkillLogRepository.write(
                        db,
                        project_id=p_id,
                        skill_id=step.agent_id,
                        agent_id=step.agent_id,
                        success=record.success,
                        summary=f"{step.agent_id} executed via Motor Subsystem",
                        data={
                            "input": record.input_data,
                            "output": record.output_data,
                            "errors": record.errors
                        },
                        duration_s=record.duration_s
                    )
                await ws_manager.broadcast_skill_trace(
                    job_id=str(p_id),
                    skill_id=step.agent_id,
                    success=record.success,
                    summary=f"{step.agent_id} action completed",
                    duration_s=round(record.duration_s, 3)
                )
            except Exception as e:
                _log.warning(f"Motor log persistence failed: {e}")

        asyncio.create_task(_persist_motor_log())
        return record
