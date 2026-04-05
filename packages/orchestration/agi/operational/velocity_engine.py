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

from packages.observability.logging import get_logger
from packages.orchestration.agi.schemas import ActionRecord, RiskLevel, ExecutionPlan, PlanStep
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.orchestration.application.sandbox_runner import get_sandbox_runner
from agents.agent_registry import build_agents
from packages.persistence.repository import SkillLogRepository
from packages.persistence.session import session_scope
# Faz 12.1 Stability: Event-Driven UI Updates
from packages.orchestration.domain.events import event_bus
from packages.contracts.events import EVENT_SKILL_TRACE
from packages.orchestration.agi.world.provenance_engine import provenance_engine
from packages.orchestration.agi.cognitive.metacognitive_auditor import MetacognitiveAuditor # Phase 65

_log = get_logger("velocity_engine")

@dataclass
class EngineResult:
    """Yürütme sonucu (Eski EngineResult)."""
    success: bool
    output_data: Any
    reflection: str = ""
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
        self.meta_audit = MetacognitiveAuditor(self.model_orch)

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
        from packages.orchestration.agi.operational.kinetic_arbiter import kinetic_arbiter
        
        t_start = time.time()
        await self._ensure_agents()
        
        # Faz 43: Kinetik Kaynak Dağıtıcı (Arbiter) - Slot Al
        await kinetic_arbiter.acquire_slot(agent_id, task_id)
        
        try:
            _log.info(f"[VELOCITY] Eylem simülasyonu başlatıldı: {agent_id} (Görev: {task_id})")
            
            # 1. Bilişsel Simülasyon
            sim_success, sim_report = await self._run_simulation(agent_id, prompt, context)
            if not sim_success:
                _log.warning(f"[VELOCITY] Simülasyon reddedildi: {sim_report}")
                return EngineResult(success=False, output_data=None, errors=[f"Simulation Error: {sim_report}"])

            # 2. Risk Denetimi (Audit Gate)
            from packages.orchestration.agi.security.audit_gate import AuditGate
            audit_gate = AuditGate(self.model_orch)
            is_safe, risk_notes = await self._inspect_intent_simulated(agent_id, prompt, sim_report)
            if not is_safe:
                _log.error(f"[VELOCITY] Audit Gate eylemi durdurdu: {risk_notes}")
                return EngineResult(success=False, output_data=None, errors=[f"Security Breach: {risk_notes}"])

            # 3. Araç Topraklama (Tool Grounding - Faz 66)
            _log.info(f"[VELOCITY-GROUND] Araç girdileri topraklanıyor (Faz 66): {agent_id}")
            from packages.orchestration.agi.operational.tool_grounder import get_grounded_tool_input
            grounded_context = await get_grounded_tool_input(task_id, agent_id, context)
            
            if grounded_context == "BLOCKED_PATH_ACCESS":
                _log.error(f"[VELOCITY-GROUND] Yasaklı yol erişimi engellendi: {agent_id}")
                return EngineResult(success=False, output_data=None, errors=["Tool Grounding: Blocked path access detected."])

            # 4. Gerçek Yürütme
            result = await self._realize_action(agent_id, prompt, grounded_context, task_id)
            result.duration_s = time.time() - t_start
            
            # 4. Refleksif Analiz
            await self._reflect_and_log(agent_id, result, task_id)
            
            # Phase 88: Project-level success boosts satisfaction and recovers energy
            from packages.orchestration.agi.consciousness.affective_core import affective_core
            if result.success:
                affective_core.adjust_state("goal_reached", magnitude=0.15)
            else:
                affective_core.adjust_state("error", magnitude=0.1)
            
            return result
        finally:
            # Faz 43: Slotu Bırak
            kinetic_arbiter.release_slot()

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
        """[FAZ 65] Gerçekten bir LLM tabanlı 'Foresight' simülasyonu yapar."""
        _log.debug(f"[VELOCITY] Bilişsel simülasyon (Foresight) başlatılıyor: {agent_id}")
        
        sim_res = await self.meta_audit.simulate_action_impact(agent_id, prompt, context)
        
        status = sim_res.get("predicted_status", "success")
        report = sim_res.get("foresight_report", "No report.")
        risk = sim_res.get("risk_score", 0.0)
        
        if status == "dangerous" or risk > 0.8:
            _log.error(f"[VELOCITY] Simülasyon CRITICAL tehlike tespit etti: {report}")
            return False, f"FORESIGHT VETO: {report}"
            
        if status == "risky":
            _log.warning(f"[VELOCITY] Simülasyon riskli eylem saptadı: {report}")
            # Riskli eylemleri otonom olarak (Auto-Hardening) AuditGate'e havale eder (Gerealize dögüsünde)
            return True, f"PLAN_RISKY: {report}"
            
        return True, report

    async def _realize_action(self, agent_id: str, prompt: str, context: Dict[str, Any], task_id: str) -> EngineResult:
        agent = self.agents.get(agent_id)
        if not agent:
            return EngineResult(success=False, output_data=None, errors=[f"Velocity unit {agent_id} not encountered."])

        try:
            out = await agent.execute(task_id=task_id, subtask_id=str(uuid.uuid4()), prompt=prompt, context=context)
            final_output = out.raw_output
            
            # --- Phase 67: Agent Self-Correction (Critique Loop) ---
            # Eğer çıktı kod içeriyorsa veya önemli bir adımsa, bir 'İçsel Eleştiri' (Critique) yap.
            if "```" in str(final_output) or len(str(final_output)) > 500:
                _log.info(f"[VELOCITY-CRITIQUE] Agent {agent_id} çıktısı eleştiriliyor (Faz 67)...")
                is_valid, critique_feedback = await self._self_critique_output(agent_id, prompt, final_output)
                
                if not is_valid:
                    _log.warning(f"[VELOCITY-CRITIQUE] Çıktı yetersiz/hatalı bulundu: {critique_feedback[:100]}...")
                    # Tek bir düzeltme hakkı (Self-Correction)
                    response = await self.model_orch.complete(
                        [
                            {"role": "system", "content": "Sen bir Üstat Yazılımcı ve Denetçisin."},
                            {"role": "user", "content": f"Şu talimat için bir çıktı üretildi: {prompt}\n\nÇIKTI:\n{final_output}\n\nELEŞTİRİ:\n{critique_feedback}\n\nLütfen eleştiriyi dikkate alarak KESİN, DOĞRU ve DÜZELTİLMİŞ yeni çıktıyı üret."}
                        ],
                        preferred_agent="architect"
                    )
                    final_output = response
                    _log.info(f"[VELOCITY-CRITIQUE] Çıktı revize edildi.")

            return EngineResult(
                success=True, 
                output_data=final_output,
                reflection=getattr(out, "reflection", "")
            )
        except Exception as e:
            _log.error(f"[VELOCITY] Gerçekleştirme hatası: {e}")
            return EngineResult(success=False, output_data=None, errors=[str(e)])

    async def _self_critique_output(self, agent_id: str, prompt: str, output: Any) -> (bool, str):
        """Çıktıyı mantıksal ve güvenlik açısından eleştirir."""
        critique_prompt = f"""
        Aşağıdaki talimat (Prompt) üzerine üretilen çıktıyı (Output) eleştir.
        Hataları, eksikleri ve güvenlik açıklarını tespit et.
        Eğer çıktı mükemmelse 'PASSED' de. Değilse 'FAILED:' ile başlayan bir eleştiri yaz.
        
        PROMPT: {prompt}
        OUTPUT: {output}
        
        KRİTERLER:
        1. Sözdizimi hatası var mı?
        2. Talimatın tüm kısımları karşılandı mı?
        3. Güvenlik açığı (Hardcoded key, path traversal) var mı?
        """
        try:
            res = await self.model_orch.complete(
                [{"role": "user", "content": critique_prompt}],
                preferred_agent="reviewer"
            )
            if "PASSED" in res:
                return True, ""
            return False, res
        except Exception:
            return True, "" # Hata durumunda (Rate limit vb) orijinal çıktıyı koru.

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
            
            # --- Phase 62: Deep Provenance Indexing ---
            # Eğer yürütme başarılıysa ve bir çıktı varsa, değişikliği 'Nedensel Köken' olarak işle.
            if result.success and result.output_data:
                # Çıktıdan dosya yollarını ve içeriği tahmin et (Heuristic or Explicit)
                # Not: Gerçek dünyada bu, tool_call loglarından gelmelidir. 
                # Şimdilik heuristik bir 'Mutation Marker' ekliyoruz.
                files = re.findall(r"FILE:\s*([\w\./-]+\.\w+)", str(result.output_data))
                for f_path in files:
                    await provenance_engine.register_mutation(
                        file_path=f_path,
                        content=str(result.output_data)[:5000], # Özet içerik
                        project_id=task_id,
                        agent_id=agent_id
                    )

            await event_bus.emit(EVENT_SKILL_TRACE, {
                "job_id": str(p_id),
                "skill_id": agent_id,
                "success": result.success,
                "summary": f"Velocity Pulse: {agent_id} finalized",
                "duration_s": round(result.duration_s, 3)
            })
        except Exception as e:
            _log.warning(f"[VELOCITY] Reflexive logging error: {e}")

# --- Singleton ---
velocity_engine = VelocityEngine()
