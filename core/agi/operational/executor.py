import asyncio
import time
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from core.agi.schemas import ExecutionPlan, PlanStep, ActionRecord, RiskLevel
from core.sandbox_runner import get_sandbox_runner
from agents.agent_registry import build_agents
from db.repository import SkillLogRepository
from db.session import session_scope
from api.ws_manager import ws_manager
import uuid

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
            tool_used=step.agent_id, # Agent or Tool is the primary 'tool' here
            input_data=step.params,
            timestamp=datetime.now(timezone.utc)
        )

        try:
            # --- Dinamik Araç Kontrolü (Phase 12.4) ---
            from core.agi.operational.tool_weaver import tool_registry
            dynamic_tool = tool_registry.get_tool(step.agent_id)
            
            if dynamic_tool:
                _log.info(f"Otonom araç çalıştırılıyor: {step.agent_id}")
                with open(dynamic_tool["path"], "r", encoding="utf-8") as f:
                    code = f.read()
                
                # Script içindeki main() fonksiyonunu çağıracak bir wrapper ekle
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
                    exit(1)
                """
                
                res = await self.sandbox.run_python(wrapper)
                if res.success:
                    # Çıktıyı parse et
                    import re
                    match = re.search(r"---RESULT_START---\n(.*?)\n---RESULT_END---", res.stdout, re.DOTALL)
                    record.output_data = json.loads(match.group(1)) if match else res.stdout
                    record.success = True
                else:
                    record.success = False
                    record.errors.append(res.stderr or "Unknown tool error")

            else:
                # Normal Ajan Yürütme
                agent = self.agents.get(step.agent_id)
                if not agent:
                    # Dinamik ajan yükleme logic'i (Phase 12.4: Eğer agent yoksa, tool sentezle!)
                    from core.agi.operational.tool_weaver import tool_weaver
                    weave_res = await tool_weaver.weave_capability(f"Yeni ajan/araç gereksinimi: {step.agent_id}", step.agent_id)
                    if weave_res["status"] == "success":
                        # Rekürsif olarak tekrar dene (yeni araç artık registry'de)
                        return await self._execute_step(step, plan_id)
                    else:
                        raise ValueError(f"Agent not found and synthesis failed: {step.agent_id}")

                # Execution context (Shared state and previous results)
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
        
        # --- Faz 13: Kalıcı Beceri Loglama (Async) ---
        async def _persist_log():
            try:
                # plan_id UUID formatında olmalı
                try:
                    p_id = uuid.UUID(plan_id)
                except ValueError:
                    return # Loglama hatası, ama yürütmeyi bozma
                
                async with session_scope() as db:
                    await SkillLogRepository.write(
                        db,
                        project_id=p_id,
                        skill_id=step.agent_id,
                        agent_id=step.agent_id,
                        success=record.success,
                        summary=f"{step.agent_id} executed: {'SUCCESS' if record.success else 'FAILED'}",
                        data={
                            "input": record.input_data,
                            "output": record.output_data,
                            "errors": record.errors
                        },
                        duration_s=record.duration_s
                    )
                # ── Real-time WS Broadcast ──
                await ws_manager.broadcast_skill_trace(
                    job_id=str(p_id),
                    skill_id=step.agent_id,
                    success=record.success,
                    summary=f"{step.agent_id} completed",
                    duration_s=round(record.duration_s, 3)
                )
            except Exception as e:
                _log.warning(f"Skill log persistence failed (non-blocking): {e}")

        asyncio.create_task(_persist_log())
        
        return record

from datetime import datetime, timezone
