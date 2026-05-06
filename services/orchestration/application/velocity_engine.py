"""
Velocity Engine — Phase 20 (High-Speed AGI Execution) [MIGRATED TO APPLICATION LAYER]
Simulation -> Risk Analysis -> Realization -> Reflexive Analysis
"""

import asyncio
import time
import json
import uuid
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from services.observability.logging import get_logger
from services.orchestration.domain.models import ActionRecord, RiskLevel, ExecutionPlan, PlanStep
from libs.llm.model_orchestrator import ModelOrchestrator
from services.orchestration.application.sandbox_runner import get_sandbox_runner
from services.orchestration.application.agent_discovery import build_agents
from libs.db.repositories.repository import SkillLogRepository
from libs.db.session import session_scope
from services.orchestration.domain.events import event_bus
from libs.contracts.events import EVENT_SKILL_TRACE
from services.orchestration.agi.world.provenance_engine import provenance_engine # To be moved
# from services.orchestration.agi.cognitive.metacognitive_auditor import MetacognitiveAuditor # Moved to lazy property
from services.orchestration.agi.operational.tool_executor import tool_executor
from services.governance.quality.output_schema import output_parser, AgentOutput

_log = get_logger("velocity_engine")

@dataclass
class EngineResult:
    """Yürütme sonucu."""
    success: bool
    output_data: Any
    reflection: str = ""
    errors: List[str] = field(default_factory=list)
    duration_s: float = 0.0

class VelocityEngine:
    """
    Sistemin yüksek hızlı, paralel (Swarm) yürütme katmanı.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.sandbox = get_sandbox_runner()
        self.agents = {} 
        self.simulation_mode = True 
        self._meta_audit = None

    @property
    def meta_audit(self):
        """Lazy loader for MetacognitiveAuditor to prevent circular imports."""
        if self._meta_audit is None:
            from services.orchestration.agi.cognitive.metacognitive_auditor import MetacognitiveAuditor
            self._meta_audit = MetacognitiveAuditor(self.model_orch)
        return self._meta_audit

    async def _ensure_agents(self):
        if not self.agents:
            self.agents = build_agents()

    async def simulate(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        agent_id = action.get("agent_id", "architect")
        prompt = action.get("prompt", "")
        success, report = await self._run_simulation(agent_id, prompt, context)
        return {
            "status": "success" if success else "failed",
            "summary": report,
            "simulated_at": datetime.now(timezone.utc).isoformat()
        }

    async def simulate_and_execute(self, agent_id: str, prompt: str, context: Dict[str, Any], task_id: str) -> EngineResult:
        from services.orchestration.agi.operational.kinetic_arbiter import kinetic_arbiter
        t_start = time.time()
        await self._ensure_agents()
        await kinetic_arbiter.acquire_slot(agent_id, task_id)
        try:
            _log.info(f"[VELOCITY] Eylem simülasyonu başlatıldı: {agent_id} (Görev: {task_id})")
            sim_success, sim_report = await self._run_simulation(agent_id, prompt, context)
            if not sim_success:
                return EngineResult(success=False, output_data=None, errors=[f"Simulation Error: {sim_report}"])
            from services.orchestration.agi.security.audit_gate import AuditGate
            audit_gate_srv = AuditGate(self.model_orch)
            is_safe, risk_notes = await self._inspect_intent_simulated(agent_id, prompt, sim_report)
            if not is_safe:
                return EngineResult(success=False, output_data=None, errors=[f"Security Breach: {risk_notes}"])
            from services.orchestration.agi.operational.tool_grounder import get_grounded_tool_input
            grounded_context = await get_grounded_tool_input(task_id, agent_id, context)
            if grounded_context == "BLOCKED_PATH_ACCESS":
                return EngineResult(success=False, output_data=None, errors=["Tool Grounding: Blocked path access detected."])
            result = await self._realize_action(agent_id, prompt, grounded_context, task_id)
            result.duration_s = time.time() - t_start
            await self._reflect_and_log(agent_id, result, task_id)
            from services.orchestration.agi.consciousness.affective_core import affective_core
            if result.success: affective_core.adjust_state("goal_reached", magnitude=0.15)
            else: affective_core.adjust_state("error", magnitude=0.1)
            return result
        finally:
            kinetic_arbiter.release_slot()

    async def execute_swarm(self, actions: List[Dict[str, Any]], context: Dict[str, Any], task_id: str) -> List[EngineResult]:
        tasks = []
        for action in actions:
            workers.workflow_worker.tasks.append(self.simulate_and_execute(action.get("agent_id", "architect"), action.get("prompt", ""), context, task_id))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if not isinstance(r, Exception) else EngineResult(success=False, output_data=None, errors=[str(r)]) for r in results]

    async def _run_simulation(self, agent_id: str, prompt: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        sim_res = await self.meta_audit.simulate_action_impact(agent_id, prompt, context)
        if not isinstance(sim_res, dict):
            _log.warning(f"[VELOCITY] Simulation result was not a dict, using defaults: {sim_res}")
            return True, "Nominal (Audit Bypass)"
            
        status = sim_res.get("predicted_status", "success")
        report = sim_res.get("foresight_report", "No report.")
        risk = sim_res.get("risk_score", 0.0)
        if status == "dangerous" or risk > 0.8: return False, f"FORESIGHT VETO: {report}"
        return True, report

    async def _realize_action(self, agent_id: str, prompt: str, context: Dict[str, Any], task_id: str) -> EngineResult:
        agent = self.agents.get(agent_id)
        if not agent: return EngineResult(success=False, output_data=None, errors=[f"Velocity unit {agent_id} not encountered."])
        try:
            out = await agent.execute(task_id=task_id, subtask_id=str(uuid.uuid4()), prompt=prompt, context=context)
            final_output = out.raw_output
            
            # 1. Self-Critique (If output is large or contains code)
            if "```" in str(final_output) or len(str(final_output)) > 500:
                is_valid, critique_feedback = await self._self_critique_output(agent_id, prompt, final_output)
                if not is_valid:
                    response = await self.model_orch.complete([{"role": "system", "content": "Sen bir Üstat Yazılımcı ve Denetçisin."}, {"role": "user", "content": f"Şu talimat için bir çıktı üretildi: {prompt}\n\nÇIKTI:\n{final_output}\n\nELEŞTİRİ:\n{critique_feedback}\n\nLütfen eleştiriyi dikkate alarak KESİN, DOĞRU ve DÜZELTİLMİŞ yeni çıktıyı üret."}], preferred_agent="architect")
                    final_output = response

            # 2. Parse Structured Output & Execute Tools (Phase 12.2 Integration)
            parsed: AgentOutput = output_parser.parse(str(final_output))
            if parsed.tool_calls:
                _log.info(f"[VELOCITY-REALIZATION] {len(parsed.tool_calls)} araç çağrısı saptandı. İcra ediliyor...")
                tool_results = await tool_executor.execute_calls(task_id, agent_id, parsed.tool_calls, context)
                # Sonuçları ana çıktıya enjekte et (Ajanın bir sonraki adımda görmesi için)
                parsed.quality_notes.append(f"Autonomous Tool Results: {json.dumps(tool_results)}")
                final_output = parsed.to_dict()

            return EngineResult(success=True, output_data=final_output, reflection=getattr(out, "reflection", ""))
        except Exception as e: return EngineResult(success=False, output_data=None, errors=[str(e)])

    async def _self_critique_output(self, agent_id: str, prompt: str, output: Any) -> Tuple[bool, str]:
        critique_prompt = f"Talimat: {prompt}\nÇıktı: {output}\nLütfen bu çıktıyı eleştir. Geçerliyse PASSED, değilse FAILED: <neden> şeklinde döndür."
        try:
            res = await self.model_orch.complete([{"role": "user", "content": critique_prompt}], preferred_agent="reviewer")
            if "PASSED" in res: return True, ""
            return False, res
        except: return True, ""

    async def _inspect_intent_simulated(self, agent_id: str, prompt: str, sim_report: str) -> Tuple[bool, str]:
        if "delete" in prompt.lower() and "force" not in prompt.lower():
            return False, "Data Loss Risk: 'delete' without force override."
        return True, "Safe."

    async def _reflect_and_log(self, agent_id: str, result: EngineResult, task_id: str):
        try:
            p_id = uuid.UUID(task_id)
            async with session_scope() as db:
                await SkillLogRepository.write(db, project_id=p_id, skill_id=agent_id, agent_id=agent_id, success=result.success, summary=f"Velocity Action realized via {agent_id}", data={"output": result.output_data, "errors": result.errors}, duration_s=result.duration_s)
            if result.success and result.output_data:
                files = re.findall(r"FILE:\s*([\w\./-]+\.\w+)", str(result.output_data))
                for f_path in files: await provenance_engine.register_mutation(file_path=f_path, content=str(result.output_data)[:5000], project_id=task_id, agent_id=agent_id)
            await event_bus.emit(EVENT_SKILL_TRACE, job_id=str(p_id), skill_id=agent_id, success=result.success, summary=f"Velocity Pulse: {agent_id} finalized", duration_s=round(result.duration_s, 3))
        except: pass

# --- Singleton ---
velocity_engine = VelocityEngine()
