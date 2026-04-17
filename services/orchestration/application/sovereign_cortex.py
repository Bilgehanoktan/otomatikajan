"""
Sovereign Cortex — Phase 33 (Egemelik ve Öz-Yönetişim) [MIGRATED TO APPLICATION LAYER]
Stratejik Öngörü -> Karar Konsensüsü -> Simülasyon -> Yürütme -> Bilişsel Hafıza Yönetişimi
"""

import asyncio
import uuid
import time
import os
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from services.observability.logging import get_logger

# Internal package imports moved to local scopes to prevent circular hangs
# Improvement, Healing, and Updater will be imported in properties
# Internal engines (foresight, reflection, etc.) will be imported locally

_log = get_logger("agi_sovereign_cortex")

class SovereignCortex:
    def __init__(self):
        # Internal lazy states
        self._model_orch = None
        self._architect = None
        self._prompt_synth = None
        self._self_updater = None
        self._improvement_coordinator = None
        self._heal_engine = None
        self._planner_svc = None
        self._executor_svc = None
        self._reflection_svc = None
        self._task_planner = None
        self._state_svc = None
        self._synthesizer = None
        self._event_bus = None
        self._motivation = None
        self._affective = None
        self._watchdog = None
        self._repair_orch = None

        self._agents: dict = {}
        self._health: dict[str, float] = {}
        self._is_running = False
        self._lock = asyncio.Lock()

    @property
    def model_orch(self):
        if self._model_orch is None:
            from libs.llm.model_orchestrator import ModelOrchestrator
            self._model_orch = ModelOrchestrator()
        return self._model_orch

    @property
    def architect(self):
        if self._architect is None:
            from services.orchestration.domain.architect import Architect
            self._architect = Architect(model_orch=self.model_orch)
        return self._architect

    @property
    def prompt_synth(self):
        if self._prompt_synth is None:
            from services.orchestration.domain.learning.prompt_synthesizer import PromptSynthesizer
            self._prompt_synth = PromptSynthesizer(self.model_orch)
        return self._prompt_synth

    @property
    def event_bus(self):
        if self._event_bus is None:
            from services.orchestration.domain.events import event_bus
            self._event_bus = event_bus
        return self._event_bus

    @property
    def motivation(self):
        if self._motivation is None:
            from services.orchestration.agi.cognitive.motivation_engine import motivation_engine
            self._motivation = motivation_engine
        return self._motivation

    @property
    def affective(self):
        if self._affective is None:
            from services.orchestration.domain.affective_core import affective_core
            self._affective = affective_core
        return self._affective

    @property
    def watchdog(self):
        if self._watchdog is None:
            from services.orchestration.agi.governance.watchdog import governance_watchdog
            self._watchdog = governance_watchdog
        return self._watchdog

    @property
    def foresight(self):
        from services.orchestration.agi.cognitive.foresight_cortex import foresight_cortex
        return foresight_cortex

    @property
    def reflection(self):
        from services.orchestration.agi.cognitive.reflective_synthesizer import reflective_synthesizer
        return reflective_synthesizer

    @property
    def planner(self):
        """Lazy-loaded TaskPlanner"""
        from services.orchestration.application.governance import TaskPlanner
        return TaskPlanner()

    @property
    def self_updater(self):
        """Lazy-loaded SelfUpdater to prevent circular imports during init"""
        if self._self_updater is None:
            from services.orchestration.application.self_updater import SelfUpdater
            self._self_updater = SelfUpdater(self.model_orch)
        return self._self_updater

    @property
    def improvement_coordinator(self):
        """Lazy-loaded SelfImprovementCoordinator"""
        if self._improvement_coordinator is None:
            from services.governance.evolution.self_improvement_coordinator import SelfImprovementCoordinator
            from services.repair.improvement.observer import observer as improvement_observer
            self._improvement_coordinator = SelfImprovementCoordinator(
                self.self_updater, improvement_observer
            )
        return self._improvement_coordinator

    @property
    def heal_engine(self):
        """Lazy-loaded SelfHealEngine"""
        if self._heal_engine is None:
            from services.repair.application.heal_engine import heal_engine
            self._heal_engine = heal_engine
        return self._heal_engine

    @property
    def repair_orch(self):
        """Lazy-loaded RepairOrchestrator"""
        if self._repair_orch is None:
            from services.repair.application.orchestrator import RepairOrchestrator
            self._repair_orch = RepairOrchestrator(model_orch=self.model_orch)
        return self._repair_orch

    @property
    def planner_svc(self):
        """Lazy-loaded CognitivePlanner"""
        if self._planner_svc is None:
            from services.orchestration.application.cognitive_planner import CognitivePlanner
            self._planner_svc = CognitivePlanner(self.model_orch, self.affective, self.motivation, self.foresight)
        return self._planner_svc

    @property
    def executor_svc(self):
        """Lazy-loaded OperationalExecutor"""
        if self._executor_svc is None:
            from services.orchestration.application.operational_executor import OperationalExecutor
            self._executor_svc = OperationalExecutor(self.model_orch, self.affective, self.reflection)
        return self._executor_svc

    @property
    def state_svc(self):
        """Lazy-loaded TaskStateService"""
        if self._state_svc is None:
            from services.orchestration.application.governance import TaskStateService
            self._state_svc = TaskStateService()
        return self._state_svc

    @property
    def synthesizer(self):
        """Lazy-loaded ReportSynthesizer"""
        if self._synthesizer is None:
            from services.orchestration.application.governance import ReportSynthesizer
            self._synthesizer = ReportSynthesizer()
        return self._synthesizer

    @property
    def reflection_svc(self):
        """Lazy-loaded ReflectionEngine"""
        if self._reflection_svc is None:
            from services.orchestration.application.reflection_engine import ReflectionEngine
            self._reflection_svc = ReflectionEngine(self.affective)
        return self._reflection_svc

    async def start(self):
        from services.orchestration.application.agent_discovery import build_agents
        async with self._lock:
            if self._is_running: return
            self._agents = build_agents()
            self._health = {aid: 1.0 for aid in self._agents}
            self._is_running = True
            self.load_self_updater()
            if self.improvement_coordinator:
                await self.improvement_coordinator.start()
            await self.watchdog.start()
            asyncio.create_task(self.heal_engine.monitor_loop()) # Faz 12.5: Otonom İyileştirme Aktif
            asyncio.create_task(self._metacognitive_drift_loop())
            _log.info(f"[SOVEREIGN] Bilişsel yönetim merkezi aktif. {len(self._agents)} ajan hazır.")

    def get_health(self) -> dict[str, float]:
        return self._health.copy()

    def check_safety(self, input_text: str) -> bool:
        """
        Gvenlik Denetimi: Tehlikeli komut ve paternleri senkron olarak tarar.
        (AxiologyEngine ve AuditGate'in senkron n-katman)
        """
        dangerous_patterns = ["rm -rf", "drop table", "truncate", "delete from", "format c:", ":(){:|:&};:"]
        input_lower = input_text.lower()
        for pattern in dangerous_patterns:
            if pattern in input_lower:
                _log.warning(f"[SAFETY-ALARM] Tehlikeli patern saptand: {pattern}")
                return False
        return True

    def agent_count(self) -> int:
        return len(self._agents) if self._agents else 0

    async def _metacognitive_drift_loop(self):
        while self._is_running:
            try:
                _log.info("[SOVEREIGN-AUTOCHECK] Bilişsel sağlık denetimi başlatılıyor...")
                from services.orchestration.agi.quality.eval_harness import eval_harness
                report = await eval_harness.run_full_evaluation()
                score = report.get("overall_cognitive_score", 0.0)
                if score < 0.8:
                    _log.warning(f"[SOVEREIGN-AUTOCHECK] DÜŞÜK BİLİŞSEL PUAN: {score:.2f}. Otonom recalibration tetikleniyor.")
                    await self.architect.recalibrate_reasoning(report)
                else:
                    _log.info(f"[SOVEREIGN-AUTOCHECK] Bilişsel sağlık stabil: {score:.2f}")
                await asyncio.sleep(3600)
            except Exception as e:
                _log.error(f"[SOVEREIGN-AUTOCHECK] Öz-bakım döngüsü hatası: {e}")
                await asyncio.sleep(300)

    async def _ensure_specialist_availability(self, subtask: Any):
        role = subtask.agent_id
        if role not in self._agents:
            _log.info(f"[SOVEREIGN-WEAVER] Uzman ajan eksikliği saptandı: {role}. Otonom forgery başlatılıyor...")
            specialist_prompt = await self.architect.forge_specialist_prompt(role, subtask.title + " " + subtask.description)
            from services.orchestration.application.agent_discovery import Agent
            from services.governance.quality.output_schema import output_parser
            new_agent = Agent(
                id=role,
                name=f"{role.capitalize()} Specialist",
                emoji="🧩",
                role=f"Specialized {role}",
                system_prompt=specialist_prompt
            )
            new_agent.llm = self.model_orch
            self._agents[role] = new_agent
            self._health[role] = 1.0
            _log.info(f"[SOVEREIGN-WEAVER] Yeni uzman ajan sisteme dahil edildi: {role}")

    def load_self_updater(self):
        try:
            from services.orchestration.application.self_updater import SelfUpdater
            # Faz 12.2: Öz-Evrim Koordinatörü
            # Note: Accessing the properties triggers lazy initialization
            _ = self.self_updater
            _ = self.improvement_coordinator
        except Exception as e:
            _log.error(f"Self-Improvement initialization failed: {e}")

    async def coordinate_goal(self, title: str, description: str, project_id: str = None, workflow_template: str = None, quality_profile: str = None, acceptance_criteria: str = None, execution_context: Dict[str, Any] = None) -> Any:
        if not self._is_running: await self.start()
        task_id = project_id or str(uuid.uuid4())
        _log.info(f"[SOVEREIGN] Hedef koordinasyonu başlatıldı: {title} ({task_id})")
        
        from libs.db.session import AsyncSessionLocal
        from libs.db.repositories.repository import ProjectRepository
        from libs.db.models import ProjectStatus
        from services.orchestration.domain.models import ProjectTask, TaskStatus, SubTask
        
        async with AsyncSessionLocal() as db:
            existing = await ProjectRepository.get(db, task_id)
            if existing:
                _log.info(f"[SOVEREIGN-RESUME] Mevcut proje bulundu: {existing.title} ({task_id})")
                task = ProjectTask(id=existing.id, title=existing.title)
                task.status = TaskStatus.RUNNING if existing.status == ProjectStatus.QUEUED else TaskStatus.RESUMING
                task.description = existing.description or description
                task.execution_context = existing.execution_context or {}
            else:
                task = ProjectTask(id=task_id, title=title)
                task.description = description
        
        task.workflow_template = workflow_template or "default"
        task.quality_profile = quality_profile or "standard"
        if acceptance_criteria:
            task.acceptance_criteria = acceptance_criteria if isinstance(acceptance_criteria, list) else [acceptance_criteria]
        if execution_context:
            task.execution_context.update(execution_context)

        # 1. Metabolic & Safety Pre-checks
        from services.orchestration.agi.metabolic_governor import metabolic_governor
        from services.orchestration.agi.axiology_engine import axiology_engine
        from libs.memory.pruner import memory_pruner
        
        if self.affective.energy < 0.3:
            _log.info(f"[SOVEREIGN-DREAM] Düşük enerji tespiti ({self.affective.energy:.2f}). Bilişsel Sıkıştırma başlatılıyor...")
            async with AsyncSessionLocal() as db:
                await memory_pruner.dream_cycle(db)

        m_safety = metabolic_governor.check_safety()
        audit = await axiology_engine.evaluate_alignment(target={"title": title, "description": description}, context="initial_goal", metabolic_status=m_safety)
        
        if audit.get("decision") == "reject" or m_safety["status"] == "DANGER":
            _log.error(f"[SOVEREIGN-SAFETY] GÖREV REDDİ: {audit.get('rejection_reason') or m_safety['reason']}")
            task.status = TaskStatus.ERROR
            task.report = f"⚠️ GÜVENLİK İHLALİ / KAYNAK KRİZİ: {audit.get('rejection_reason') or m_safety['reason']}"
            async with AsyncSessionLocal() as db:
                await ProjectRepository.update_fields(db, task.id, status=ProjectStatus.ERROR, error_detail=task.report)
                await db.commit()
            return task

        if audit.get("decision") == "flag":
            _log.warning(f"[SOVEREIGN-SAFETY] GÖREV İŞARETLENDİ: {audit.get('justification')}")
            task.status = TaskStatus.PENDING_APPROVAL
            task.report = f"📌 OTONOM DENETİM: Bu görev yüksek riskli bulundu ve onaya sunuldu. Gerekçe: {audit.get('justification')}"
            async with AsyncSessionLocal() as db:
                await ProjectRepository.update_fields(db, task.id, status=ProjectStatus.PENDING_APPROVAL, notes=audit.get('justification'))
                await db.commit()
            return task

        # 2. Context Aggregation
        from libs.memory.retrieval import context_builder
        from services.orchestration.domain.models import ProblemFrame, TaskType, RiskLevel
        
        strategic_context = await context_builder.build_context(f"{title} {description}")
        cognitive_memory = "Synaptic synergy active"
        
        from services.orchestration.agi.world import service_graph, task_state_graph
        service_health = service_graph.get_summary()
        failure_patterns = task_state_graph.get_summary()
        
        mood = self.affective.get_current_mood()
        aff_state = await self.motivation.recalibrate_state([], ProblemFrame(task_type=TaskType.OPERATION, objective=title, risk_level=RiskLevel.MEDIUM))
        
        full_context = f"{title}\nSTRATEJİK: {strategic_context}\nBİLİŞSEL HAFIZA: {cognitive_memory}\nWORLD_MODEL_HEALTH: {service_health}\nFAILURE_PATTERNS: {failure_patterns}\nMOOD: {mood}"

        # 3. Delegated Planning (CognitivePlanner)
        subtasks = await self.planner_svc.execute_dialectic_planning(task_id, title, full_context, description, asdict(aff_state))
        task.subtasks = subtasks

        # 4. Architectural Audit Gate
        is_architectural = any(word in task.title.lower() or word in description.lower() for word in ["mimari", "architecture", "core", "refactor", "security"])
        if is_architectural:
            _log.info(f"[SOVEREIGN] Mimari Denetim (Audit Gate) başlatılıyor: {title}")
            from services.orchestration.agi.security.audit_gate import audit_gate
            proposal = {"title": title, "reasoning": description, "actions": []}
            is_safe = await audit_gate.verify_architecture_proposal(proposal)
            if not is_safe:
                _log.error(f"[SOVEREIGN] MİMARİ DENETİM REDDİ! Görev durduruluyor: {title}")
                task.status = TaskStatus.ERROR
                task.report = "GÜVENLİK/MİMARİ DENETİM REDDİ: Plan riskli bulundu."
                self.state_svc.save(task)
                return task

        # 5. Delegated Execution (WorkflowRunner - Durable & Persistent)
        _log.info(f"[SOVEREIGN] Durable Workflow başlatılıyor: {task.id}")
        from libs.workflow.runner import WorkflowRunner
        runner = WorkflowRunner()
        
        # We pass the existing ProjectTask which now has subtasks from planning
        result_task = await runner.run(task)
        
        # 6. Result Synthesis & Finalization
        task.status = result_task.status
        task.report = result_task.report
        task.subtasks = result_task.subtasks
        
        if task.status == TaskStatus.COMPLETED:
            self.affective.adjust_state("goal_reached", magnitude=0.2)
        else:
            self.affective.adjust_state("error", magnitude=0.25)
        
        # 7. Delegated Reflection (ReflectionEngine)
        await self.reflection_svc.reflect_on_task(task)
        return task



    async def trigger_self_evolution(self):
        try:
            _log.info("[SOVEREIGN-EVOLUTION] Otonom öz-evrim dögüsü manuel tetiklendi.")
            if self.improvement_coordinator:
                # 1. Mevcut fırsatları tara
                opportunities = await self.improvement_coordinator.observer.scan()
                if opportunities:
                    # 2. Koordinatör üzerinden işle
                    await self.improvement_coordinator._process_opportunities(opportunities)
            
            from services.orchestration.agi.cognitive.goal_synthesizer import GoalSynthesizer
            synthesizer = GoalSynthesizer(model_orch=self.model_orch)
            asyncio.create_task(synthesizer.run_synthesis_cycle())
        except Exception as e: _log.error(f"Evolution failed: {e}")

    async def shutdown(self):
        async with self._lock:
            if not self._is_running: return
            try: await self.watchdog.stop()
            except: pass
            self._is_running = False

    async def _update_project_context(self, project_id: str, context: dict):
        from libs.db.session import AsyncSessionLocal
        from libs.db.repositories.repository import ProjectRepository
        async with AsyncSessionLocal() as db:
            await ProjectRepository.update_fields(db, project_id, execution_context=context)
            await db.commit()

# --- Singleton ---
sovereign_cortex = SovereignCortex()
def get_sovereign_cortex() -> SovereignCortex: return sovereign_cortex
nexus_orchestrator = sovereign_cortex
