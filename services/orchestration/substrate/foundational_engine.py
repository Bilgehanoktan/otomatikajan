"""
Orkestratör — Faz 3 (DAG Entegrasyonlu)
Plan -> Bellek Bağlamı -> DAG (Bağımlılıklı Yürütme) -> Kalite Kontrolü -> Reviewer -> Sentez
"""

import asyncio
import uuid
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from agents.specialist_agents.agent_registry import build_agents
from services.observability.logging import get_logger
from libs.llm.model_orchestrator import ModelOrchestrator
from services.governance.quality.approval_gate import approval_gate, RiskLevel
from libs.memory.retrieval import context_builder
from services.governance.quality.output_schema import output_parser, AgentOutput
from services.governance.quality.evaluator import QualityEvaluator
from services.governance.quality.scorer import QualityReport
from services.governance.quality.reviewer import ReviewerAgent

_log = get_logger("orchestrator")

# ── 1. Durumlar ve Veri Yapıları ─────────────────────────────────
from services.orchestration.agi.task_governance import (
    SovereignGoal, GovernedTask, GovernanceStatus, TaskPlanner, TaskStateService, 
    ReportSynthesizer, ProjectTask, SubTask, TaskStatus
)
from hub_cortex.skills.base import SkillRequest
from hub_cortex.skills.registry import skill_registry

# ── 2. DAG (Bağımlılık) Haritası ─────────────────────────────────
DAG_WORKFLOW = {
    "architect": [],                                  
    "backend_dev": ["architect"],                     
    "frontend_dev": ["architect"],                    
    "qa_engineer": ["backend_dev", "frontend_dev"],   
    "security": ["backend_dev", "frontend_dev"],      
    "data_eng": ["architect"],                        
    "devops": ["backend_dev", "frontend_dev"],        
    "tech_writer": ["qa_engineer", "security"],
    "system_controller": ["tech_writer"]
}

# ════════════════════════════════════════════════════════
# Orchestrator
# ════════════════════════════════════════════════════════
class Orchestrator:
    from libs.config import LLM_MAX_RETRIES
    MAX_RETRIES = LLM_MAX_RETRIES

    def __init__(self):
        self.model_orch  = ModelOrchestrator()
        self.planner     = TaskPlanner()
        self.state_svc   = TaskStateService()
        self.synthesizer = ReportSynthesizer()
        self.self_updater = None # Lazily or explicitly initialized (Faz 8 Infra)
        try:
            from sovereign_codegen.manager import CodeEngineManager
            self.ce_manager = CodeEngineManager()
        except ImportError:
            self.ce_manager = None
        self.code_engine = None  # Lazily or explicitly initialized
        self._is_running = False
        self._lock       = asyncio.Lock()
        self._agents: dict = {}
        self._health: dict[str, float] = {}
        self._quality_enabled  = True
        self._memory_enabled   = True
        self._reviewer_enabled = True

    async def start(self):
        async with self._lock:
            if self._is_running:
                return
            self._agents = build_agents()
            self._health = {aid: 1.0 for aid in self._agents}
            self._is_running = True
        
        # Kod motorunu da burada başlat (Faz 6)
        try:
            from sovereign_codegen import init_sovereign_codegen
            self.code_engine = init_sovereign_codegen(self.model_orch)
            _log.info("[OK] Kod uretim motoru entegre edildi.")
        except ImportError:
            _log.warning("[WARN] Kod uretim motoru bulunamadi.")
            
        # Self-Updater başlat (Faz 8 Infra)
        try:
            from services.orchestration.application.self_updater import SelfUpdater
            import os
            self.self_updater = SelfUpdater(
                model_orch=self.model_orch,
                project_root=os.path.dirname(os.path.dirname(__file__))
            )
            _log.info("[OK] Self-Updater (Oz-Guncelleme) hazir.")
        except Exception as _su_err:
            _log.warning(f"[WARN] Self-Updater bashlatilamadi: {_su_err}")
            
        _log.info(f"[OK] {len(self._agents)} ajan hazir.")

    async def shutdown(self):
        _log.info("Bakirsin! Orkestrator kapatiliyor.")

    def list_tasks(self) -> list[ProjectTask]:
        """Tüm görevleri listele — routes ve telegram tarafından kullanılır."""
        return self.state_svc.all_tasks()

    def get_task(self, task_id: str) -> ProjectTask | None:
        """Belirli bir görevi ID ile getir."""
        return self.state_svc.get(task_id)

    def get_health(self) -> dict[str, float]:
        """Heal Engine için kritik: Mevcut ajanların sağlık skorlarını döner."""
        return self._health.copy()

    def agent_count(self) -> int:
        """Kayıtlı ajan sayısını döner."""
        return len(self._agents) if hasattr(self, "_agents") else 0

    async def run_project(self, title: str, description: str, project_id: str | None = None,
                          heal_engine=None,
                          workflow_template="default", quality_profile="standard",
                          acceptance_criteria=None, execution_context=None,
                          db_subtask_map: dict | None = None) -> ProjectTask:
        # Faz 12.1 Hardening: Worker ortamında start() çağrılmamış olabilir
        if not self._is_running:
            await self.start()
            
        task          = ProjectTask(
            id=project_id or str(uuid.uuid4()), 
            title=title,
            workflow_template=workflow_template,
            quality_profile=quality_profile,
            acceptance_criteria=acceptance_criteria or [],
            execution_context=execution_context or {}
        )
        task.subtasks = self.planner.plan(title, description)
        
        # db_subtask_map gelmişse SubTask nesnelerine ekle
        if db_subtask_map:
            for st in task.subtasks:
                if st.agent_id in db_subtask_map:
                    st.db_subtask_id = db_subtask_map[st.agent_id]

        task.status   = TaskStatus.RUNNING
        self.state_svc.save(task)

        events = {st.agent_id: asyncio.Event() for st in task.subtasks}
        shared_context = "" 

        async def _dag_node(st: SubTask):
            dependencies = DAG_WORKFLOW.get(st.agent_id, [])
            for dep_id in dependencies:
                if dep_id in events:
                    await events[dep_id].wait()
            
            # Önceki tamamlanmış subtask'lardan bağlam oluştur
            current_context = "\n".join([
                f"[{s.agent_id}]: {s.result}" 
                for s in task.subtasks 
                if s.status == TaskStatus.DONE
            ])
            
            await self._run_subtask(st, shared_context=current_context, heal_engine=heal_engine, project_id=task.id, task_context=task)
            events[st.agent_id].set()

        # Tüm subtask'larını paralel (DAG sırasıyla) başlat
        await asyncio.gather(*[_dag_node(st) for st in task.subtasks])
        
        # Herhangi bir subtask failed ise ana görev FAILED veya PARTIAL_COMPLETE sayılmalı
        has_failures = any(st.status == TaskStatus.FAILED for st in task.subtasks)
        task.status = TaskStatus.FAILED if has_failures else TaskStatus.DONE
        
        task.report = self.synthesizer.synthesize(task)
        
        # Belleğe kaydet (Faz 6)
        if self._memory_enabled:
            for st in task.subtasks:
                if st.status == TaskStatus.DONE:
                    await self._save_to_memory(st.structured, task.id)
                    
        return task

    async def _run_subtask(self, st: SubTask, shared_context: str = "", heal_engine=None, project_id: str | None = None, task_context: ProjectTask | None = None):
        """Alt görevi yürütür — Onay Kapısı ve Kalite Kontrolü dahil."""
        st.status = TaskStatus.RUNNING
        try:
            # 1. Onay Kapısı (Faz 3: Human-in-the-loop)
            risk = await self._evaluate_risk_semantically(st.prompt)
            
            # Policy-based approval check (Faz 12.1)
            policy_requires_review = False
            if task_context:
                try:
                    from services.governance.quality.approval_gate import evaluate_policy
                    policy_requires_review = evaluate_policy(
                        workflow=task_context.workflow_template,
                        profile=task_context.quality_profile,
                        risk=risk
                    )
                except ImportError:
                    pass
            
            if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) or policy_requires_review:
                _log.info(f"[RISK] Onay bekleniyor... (Agent: {st.agent_id})")
                req = await approval_gate.request(
                    operation=f"agent_task:{st.agent_id}",
                    description=st.prompt[:200],
                    payload={"agent_id": st.agent_id, "prompt": st.prompt},
                    requested_by="orchestrator",
                    risk_override=risk
                )
                if not approval_gate.is_allowed(req):
                    st.status = TaskStatus.FAILED
                    st.result = f"İnsan onayı reddedildi veya zaman aşımına uğradı. (Reason: {getattr(req, 'rejection_reason', 'N/A')})"
                    _log.warning(f"❌ İşlem reddedildi: {st.agent_id}")
                    return

            # 2. Yürütme (Ajan Katmanı)
            agent = self._agents.get(st.agent_id)
            if not agent:
                from services.orchestration.agency.loader import agency_loader
                spec_data = agency_loader.get_agent(st.agent_id)
                if spec_data:
                    from agents.specialist_agents.agent_registry import Agent
                    agent = Agent(
                        id=spec_data["id"],
                        name=spec_data["name"],
                        role=spec_data.get("role", spec_data.get("category", "Specialist")),
                        system_prompt=spec_data["system_prompt"],
                        emoji=spec_data.get("emoji", "📧")
                    )
                    self._agents[st.agent_id] = agent
                else:
                    try:
                        from services.orchestration.agency.factory import get_specialist_factory
                        factory = get_specialist_factory(self.model_orch)
                        spec_data = await factory.build_specialist(st.agent_id, st.prompt)
                        if spec_data:
                            from agents.specialist_agents.agent_registry import Agent
                            agent = Agent(
                                id=spec_data["id"],
                                name=spec_data["name"],
                                role=spec_data.get("role", "Dynamic Specialist"),
                                system_prompt=spec_data["system_prompt"],
                                emoji=spec_data.get("emoji", "🧠")
                            )
                            self._agents[st.agent_id] = agent
                        else:
                            raise ValueError(f"Farkli bir ajan bulunamadi: {st.agent_id}")
                    except Exception as fe:
                        _log.error(f"[FAIL] Dinamik ajan uretimi hatasi: {fe}")
                        raise ValueError(f"Ajan bulunamadı: {st.agent_id}")

            agent.llm = self.model_orch
            
            # ── 3. Skill Preflight (Phase 12.2 Integration) ──
            skill_context = {
                "shared_context": shared_context,
                "memories": [],
                "file_hits": [],
            }
            preflight_req = SkillRequest(
                task_type="subtask_preflight",
                title=st.agent_id,
                description=st.prompt,
                project_id=project_id,
                agent_id=st.agent_id,
                context=skill_context
            )
            skill_insights = await self._run_skill_preflight(preflight_req)
            if skill_insights:
                shared_context += f"\\n\\n=== Skill Destekleri ===\\n{skill_insights}"

            # 4. Bellek Enjeksiyonu (Faz 3 & 6)
            enriched_prompt = st.prompt
            if self._memory_enabled:
                from libs.memory.retrieval import context_builder
                enriched_prompt = await context_builder.build_context(
                    agent_id=st.agent_id,
                    task_text=st.prompt,
                    project_id=getattr(self, "_task_id", None)
                )
            
            ctx_dict = {
                "requirements": enriched_prompt,
                "shared_context": shared_context
            }
            t_start = time.time()
            out = await agent.execute(
                task_id=project_id or st.id, 
                subtask_id=st.id, 
                context=ctx_dict,
                project_id=project_id
            )
            duration = time.time() - t_start
            
            res = output_parser.parse(agent_id=st.agent_id, raw=out.raw_output)
            st.result     = res.summary
            st.structured = res
            
            if self._quality_enabled and any(kw in out.raw_output for kw in ["def ", "class ", "import "]):
                from services.orchestration.application.sandbox_runner import SandboxRunner
                sbox = SandboxRunner()
                lint_res = await sbox.run_ruff_check(out.raw_output)
                if not lint_res.success:
                    st.status = TaskStatus.FAILED
                    st.result = f"Kod kalite kontrolü (Ruff) başarısız oldu. Lütfen kodu düzeltin.\\nDetaylar: {lint_res.stdout[:200]}"
                    st.quality_score = 0.0
                    return 

            st.status = TaskStatus.DONE 
            if self._quality_enabled:
                score, report = await self._check_quality(res)
                st.quality_score = score
                st.quality_detail = report.to_dict() if hasattr(report, "to_dict") else {}
                from libs.config import QUALITY_PASS_THRESHOLD
                if self._reviewer_enabled and score < QUALITY_PASS_THRESHOLD:
                    new_content, new_score, was_revised, r_notes = await self._run_reviewer(
                        res, report,
                        task_context.workflow_template if task_context else "default",
                        task_context.quality_profile if task_context else "standard",
                        task_context.acceptance_criteria if task_context else []
                    )
                    if was_revised:
                        st.result = new_content
                        st.quality_score = new_score
                        st.reviewed = True
                        st.review_notes = r_notes

            # DB'ye kaydet (Eğer db_subtask_id atanmışsa Faz 12.1)
            if st.db_subtask_id:
                try:
                    from libs.db.session import AsyncSessionLocal as get_db_session
                    from libs.db.repositories.repository import SubTaskRepository
                    async with get_db_session() as db:
                        await SubTaskRepository.mark_done(
                            db=db,
                            subtask_id=st.db_subtask_id,
                            result=st.result[:5000],
                            provider="orchestrator",
                            input_tokens=0,
                            output_tokens=0,
                            cost_usd=0.0,
                            latency_s=duration,
                            recovered=False,
                            quality_score=st.quality_score,
                            quality_detail=st.quality_detail,
                            reviewed=st.reviewed,
                            review_notes=st.review_notes
                        )
                except Exception as db_err:
                    _log.error(f"❌ DB mark_done hatası (Ajan: {st.agent_id}): {db_err}")

            if heal_engine:
                heal_engine.on_subtask_success(st.agent_id, duration_s=duration)

        except PermissionError as pe:
            _log.error(f"Bütçe Hatası ({st.agent_id}): {pe}")
            st.status = TaskStatus.FAILED
            st.result = f"BÜTÇE AŞILDI: {str(pe)}"
        except Exception as e:
            _log.error(f"Ajan hatası ({st.agent_id}): {e}")
            st.status = TaskStatus.FAILED
            st.result = str(e)
            if st.db_subtask_id:
                try:
                    from libs.db.session import AsyncSessionLocal as get_db_session
                    from libs.db.repositories.repository import SubTaskRepository
                    async with get_db_session() as db:
                        await SubTaskRepository.mark_failed(
                            db=db,
                            subtask_id=st.db_subtask_id,
                            result=st.result[:1000],
                            attempts=getattr(st, 'attempts', 0)
                        )
                except Exception as db_err:
                    _log.error(f"❌ DB mark_failed hatası: {db_err}")
            current_h = self._health.get(st.agent_id, 1.0)
            self._health[st.agent_id] = max(0.0, current_h - 0.2)
            if heal_engine:
                await heal_engine.on_subtask_error(st.agent_id, str(e))

    async def _check_quality(self, structured):
        evaluator = QualityEvaluator(self.model_orch)
        report = await evaluator.evaluate(structured)
        return report.total_score, report

    async def _run_reviewer(self, structured, quality_report, workflow_template="default", quality_profile="standard", acceptance_criteria=None):
        try:
            reviewer = ReviewerAgent(self.model_orch)
            res = await reviewer.review(
                structured, 
                quality_report,
                workflow_template=workflow_template,
                quality_profile=quality_profile,
                acceptance_criteria=acceptance_criteria or []
            )
            return res.final_output, res.final_score, res.revisions > 0, getattr(res, "reviewer_notes", [])
        except Exception as e:
            _log.warning(f"⚠️ Reviewer hatası: {e}")
            score = quality_report.total_score if quality_report else 0.5
            return structured.summary if hasattr(structured, 'summary') else str(structured), score, False, []

    async def _save_to_memory(self, structured, project_id):
        if not structured or not self._memory_enabled: return
        try:
            await context_builder.save_agent_output(agent_id=structured.agent_id, output=structured, project_id=project_id)
        except Exception as e:
            _log.error(f"Belleğe kaydetme hatası: {e}")

    async def _evaluate_risk_semantically(self, prompt: str) -> RiskLevel:
        risk_prompt = f"Risk analizi: {prompt}"
        try:
            response = await self.model_orch.generate(risk_prompt)
            if "CRITICAL" in response: return RiskLevel.CRITICAL
            if "HIGH" in response: return RiskLevel.HIGH
            if "MEDIUM" in response: return RiskLevel.MEDIUM
        except Exception:
            if any(w in prompt.lower() for w in ["delete", "drop", "rm -rf"]):
                return RiskLevel.HIGH
        return RiskLevel.LOW

    def load_self_updater(self):
        try:
            from services.orchestration.application.self_updater import SelfUpdater
            self.self_updater = SelfUpdater(model_orch=self.model_orch)
        except Exception as e:
            _log.error(f"SelfUpdater load failed: {e}")

    async def _run_skill_preflight(self, req: SkillRequest) -> str:
        from hub_cortex.skills.router import skill_router
        suggested_ids = skill_router.suggest(req)
        insights = []
        for sid in suggested_ids:
            if sid not in ["optimization", "file_search", "vault_memory"]:
                continue
            try:
                # registry.execute handles logging and timing automatically
                res = await skill_registry.execute(sid, req)
                if res.success:
                    insights.append(f"[{sid.upper()}]: {res.summary}")
            except Exception as e:
                _log.warning(f"Skill preflight hatası ({sid}): {e}")
        return "\\n".join(insights)

# --- Singleton ---
orchestrator = Orchestrator()

def get_orchestrator() -> Orchestrator:
    return orchestrator
