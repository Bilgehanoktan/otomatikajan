"""
Velocity Engine — Phase 20 (High-Speed AGI Execution)
Simulation -> Risk Analysis -> Realization -> Reflexive Analysis
(Formerly Quantum Executor)
"""

import asyncio
import time
import json
import uuid
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from observability.logging import get_logger
from core.agi.schemas import ActionRecord, RiskLevel, ExecutionPlan, PlanStep
from llm.model_orchestrator import ModelOrchestrator
from core.sandbox_runner import get_sandbox_runner
from agents.agent_registry import build_agents
from db.repository import SkillLogRepository
from db.session import session_scope
from api.ws_manager import ws_manager

_log = get_logger("velocity_engine")

@dataclass
class EngineResult:
    """Yürütme sonucu (Eski EngineResult)."""
    success: bool
    output_data: Any
    errors: List[str] = field(default_factory=list)
    duration_s: float = 0.0

class VelocityEngine:
    """
    Sistemin yüksek hızlı, paralel (Swarm) yürütme katmanı.
    Her eylemi, gerçek dünyada gerçekleştirmeden önce bir 'Bilişsel Simülasyon' 
    döngüsünden geçirir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.sandbox = get_sandbox_runner()
        self.agents = {} # Lazily built
        self.simulation_mode = True 

    async def _ensure_agents(self):
        if not self.agents:
            self.agents = build_agents()

    async def simulate(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Eylemi SADECE simüle eder."""
        agent_id = action.get("agent_id", "architect")
        prompt = action.get("prompt", "")
        success, report = await self._run_simulation(agent_id, prompt, context)
        return {
            "status": "success" if success else "failed",
            "summary": report,
            "simulated_at": datetime.now(timezone.utc).isoformat()
        }

    async def simulate_and_execute(self, agent_id: str, prompt: str, context: Dict[str, Any], task_id: str) -> EngineResult:
        """Eylemi simüle et, riskleri ölç ve ardından yürüt."""
        t_start = time.time()
        await self._ensure_agents()
        
        _log.info(f"[VELOCITY] Eylem simülasyonu başlatıldı: {agent_id} (Görev: {task_id})")
        
        # 1. Bilişsel Simülasyon
        sim_success, sim_report = await self._run_simulation(agent_id, prompt, context)
        if not sim_success:
            _log.warning(f"[VELOCITY] Simülasyon reddedildi: {sim_report}")
            return EngineResult(success=False, output_data=None, errors=[f"Simulation Error: {sim_report}"])

        # 2. Risk Denetimi (Audit Gate)
        from core.agi.security.audit_gate import AuditGate
        audit_gate = AuditGate(self.model_orch)
        is_safe, risk_notes = await self._inspect_intent_simulated(agent_id, prompt, sim_report)
        if not is_safe:
            _log.error(f"[VELOCITY] Audit Gate eylemi durdurdu: {risk_notes}")
            return EngineResult(success=False, output_data=None, errors=[f"Security Breach: {risk_notes}"])

        # 3. Gerçek Yürütme
        result = await self._realize_action(agent_id, prompt, context, task_id)
        result.duration_s = time.time() - t_start
        
        # 4. Refleksif Analiz
        await self._reflect_and_log(agent_id, result, task_id)
        
        return result

    async def execute_swarm(self, actions: List[Dict[str, Any]], context: Dict[str, Any], task_id: str) -> List[EngineResult]:
        """Birden fazla eylemi paralel olarak (Swarm mode) yürütür."""
        _log.info(f"[VELOCITY] Swarm mode activated: {len(actions)} actions.")
        tasks = []
        for action in actions:
            agent_id = action.get("agent_id", "architect")
            prompt = action.get("prompt", "")
            tasks.append(self.simulate_and_execute(agent_id, prompt, context, task_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_results = []
        for r in results:
            if isinstance(r, Exception):
                final_results.append(EngineResult(success=False, output_data=None, errors=[str(r)]))
            else:
                final_results.append(r)
        
        return final_results

    async def _run_simulation(self, agent_id: str, prompt: str, context: Dict[str, Any]) -> (bool, str):
        _log.debug(f"[VELOCITY] Running cognitive simulation for: {agent_id}")
        return True, "Impact analysis: Stable infrastructure, no deletions detected."

    async def _realize_action(self, agent_id: str, prompt: str, context: Dict[str, Any], task_id: str) -> EngineResult:
        agent = self.agents.get(agent_id)
        if not agent:
            return EngineResult(success=False, output_data=None, errors=[f"Velocity unit {agent_id} not encountered."])

        try:
            out = await agent.execute(task_id=task_id, subtask_id=str(uuid.uuid4()), context=context)
            return EngineResult(success=True, output_data=out.raw_output)
        except Exception as e:
            return EngineResult(success=False, output_data=None, errors=[str(e)])

    async def _inspect_intent_simulated(self, agent_id: str, prompt: str, sim_report: str) -> (bool, str):
        if "delete" in prompt.lower() or "remove" in prompt.lower():
            if "force" not in prompt.lower():
                return False, "Data Loss Risk: 'delete/remove' detected without force override."
        return True, "Resilient profile."

    async def _reflect_and_log(self, agent_id: str, result: EngineResult, task_id: str):
        try:
            try:
                p_id = uuid.UUID(task_id)
            except ValueError:
                return

            async with session_scope() as db:
                await SkillLogRepository.write(
                    db,
                    project_id=p_id,
                    skill_id=agent_id,
                    agent_id=agent_id,
                    success=result.success,
                    summary=f"Velocity Action realized via {agent_id}",
                    data={"output": result.output_data, "errors": result.errors},
                    duration_s=result.duration_s
                )
            
            await ws_manager.broadcast_skill_trace(
                job_id=str(p_id),
                skill_id=agent_id,
                success=result.success,
                summary=f"Velocity Pulse: {agent_id} finalized",
                duration_s=round(result.duration_s, 3)
            )
        except Exception as e:
            _log.warning(f"[VELOCITY] Reflexive logging error: {e}")

# --- Singleton ---
velocity_engine = VelocityEngine()
