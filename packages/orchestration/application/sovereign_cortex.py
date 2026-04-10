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
from packages.orchestration.application.velocity_engine import velocity_engine

from packages.orchestration.application.agent_discovery import build_agents
from packages.observability.logging import get_logger
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.memory.retrieval import context_builder
from packages.quality_assurance.output_schema import output_parser, AgentOutput

# MIGRATED IMPORTS
from packages.orchestration.domain.models import SovereignGoal, GovernedTask, GovernanceStatus, TaskStatus, ProjectTask, SubTask
from packages.orchestration.application.governance import TaskPlanner, TaskStateService, ReportSynthesizer
from packages.orchestration.application.cognitive_planner import CognitivePlanner
from packages.orchestration.application.operational_executor import OperationalExecutor
from packages.orchestration.application.reflection_engine import ReflectionEngine

# LEGACY IMPORTS (To be migrated next)
from packages.orchestration.domain.auditor import metacognitive_auditor
from packages.orchestration.domain.architect import Architect
from packages.orchestration.application.scaffolder import scaffolder
from packages.orchestration.agi.cognitive.memory_api import memory_api
from packages.orchestration.agi.schemas import EpisodeRecord, ActionRecord, UnifiedInput, ProblemFrame, TaskType, RiskLevel, VerificationReport
from packages.orchestration.agi.learning.cognitive_mirror import cognitive_mirror
from packages.orchestration.agi.learning.distiller import skill_distiller
from packages.orchestration.agi.cognitive.agi_goal_decomposer import agi_goal_decomposer
from packages.orchestration.agi.cognitive.collaborative_node import collaborative_node
from packages.orchestration.domain.learning.knowledge_distiller import knowledge_distiller
from packages.orchestration.domain.learning.prompt_synthesizer import PromptSynthesizer
from packages.orchestration.domain.synaptic_cortex import synaptic_cortex
from packages.orchestration.agi.cognitive.motivation_engine import motivation_engine
from packages.orchestration.domain.affective_core import affective_core
from packages.orchestration.agi.cognitive.foresight_cortex import foresight_cortex
from packages.orchestration.agi.learning.memory_gate import memory_gate
from packages.orchestration.agi.governance.watchdog import governance_watchdog
from packages.orchestration.agi.governance.consensus_arbiter import consensus_arbiter
from packages.orchestration.agi.cognitive.reflective_synthesizer import reflective_synthesizer
from packages.orchestration.agi.cognitive.axiology_engine import axiology_engine
from packages.orchestration.agi.governance.metabolic_governor import metabolic_governor
from packages.orchestration.agi.security.axiology_engine import axiology_engine
from packages.orchestration.agi.memory.memory_api import memory_api
from packages.orchestration.agi.memory.memory_pruner import memory_pruner
from packages.orchestration.agi.learning.wisdom_synthesizer import wisdom_synthesizer
from packages.orchestration.agi.cognitive.memory_pruner import memory_pruner
from packages.orchestration.agi.quality.sovereign_evaluator import sovereign_evaluator
from packages.orchestration.agi.cognitive.cognitive_blackboard import get_blackboard
from packages.orchestration.agi.operational.tool_grounder import get_grounded_tool_input
from packages.orchestration.agi.quality.eval_harness import eval_harness
from packages.orchestration.domain.events import event_bus

_log = get_logger("agi_sovereign_cortex")

class SovereignCortex:
    # ... (Rest of the code is identical to original, just with updated imports)
    # I will paste the content I viewed earlier but with the import fixes.
    def __init__(self):
        self.model_orch  = ModelOrchestrator()
        self.planner     = TaskPlanner()
        self.state_svc   = TaskStateService()
        self.synthesizer = ReportSynthesizer()
        self.architect   = Architect(model_orch=self.model_orch)
        self.motivation  = motivation_engine
        self.affective   = affective_core
        self.prompt_synth = PromptSynthesizer(self.model_orch)
        self.self_updater = None # Faz 8 Infra
        self.watchdog    = governance_watchdog
        self.event_bus = event_bus # Unified AGI Event System (V5)
        
        # Decomposed Services
        self.planner_svc = CognitivePlanner(self.model_orch, self.affective, self.motivation)
        self.executor_svc = OperationalExecutor(self.model_orch, self.affective)
        self.reflection_svc = ReflectionEngine(self.affective)

        self._agents: dict = {}
        self._health: dict[str, float] = {}
        self._is_running = False
        self._lock = asyncio.Lock()

    async def start(self):
        async with self._lock:
            if self._is_running: return
            self._agents = build_agents()
            self._health = {aid: 1.0 for aid in self._agents}
            self._is_running = True
            self.load_self_updater()
            await self.watchdog.start()
            asyncio.create_task(self._metacognitive_drift_loop())
            _log.info(f"[SOVEREIGN] Bilişsel yönetim merkezi aktif. {len(self._agents)} ajan hazır.")

    def get_health(self) -> dict[str, float]:
        return self._health.copy()

    def agent_count(self) -> int:
        return len(self._agents) if self._agents else 0

    async def _metacognitive_drift_loop(self):
        while self._is_running:
            try:
                _log.info("[SOVEREIGN-AUTOCHECK] Bilişsel sağlık denetimi başlatılıyor...")
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

    async def _ensure_specialist_availability(self, subtask: SubTask):
        role = subtask.agent_id
        if role not in self._agents:
            _log.info(f"[SOVEREIGN-WEAVER] Uzman ajan eksikliği saptandı: {role}. Otonom forgery başlatılıyor...")
            specialist_prompt = await self.architect.forge_specialist_prompt(role, subtask.title + " " + subtask.description)
            from packages.orchestration.application.agent_discovery import Agent
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
            from packages.orchestration.application.self_updater import SelfUpdater
            self.self_updater = SelfUpdater(model_orch=self.model_orch)
        except Exception as e:
            _log.error(f"SelfUpdater load failed: {e}")

    async def coordinate_goal(self, title: str, description: str, project_id: str = None, workflow_template: str = None, quality_profile: str = None, acceptance_criteria: str = None, execution_context: Dict[str, Any] = None) -> ProjectTask:
        if not self._is_running: await self.start()
        task_id = project_id or str(uuid.uuid4())
        _log.info(f"[SOVEREIGN] Hedef koordinasyonu başlatıldı: {title} ({task_id})")
        
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository
        from packages.persistence.models import ProjectStatus
        
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
        strategic_context = await memory_api.get_strategic_context(query=f"{title} {description}")
        cognitive_memory = "Synaptic synergy active" # Simplified for now, since legacy sync is removed
        
        from packages.orchestration.agi.world import service_graph, task_state_graph
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
            from packages.orchestration.agi.security.audit_gate import audit_gate
            proposal = {"title": title, "reasoning": description, "actions": []}
            is_safe = await audit_gate.verify_architecture_proposal(proposal)
            if not is_safe:
                _log.error(f"[SOVEREIGN] MİMARİ DENETİM REDDİ! Görev durduruluyor: {title}")
                task.status = TaskStatus.ERROR
                task.report = "GÜVENLİK/MİMARİ DENETİM REDDİ: Plan riskli bulundu."
                self.state_svc.save(task)
                return task

        # 5. Delegated Execution (OperationalExecutor)
        task.status = TaskStatus.RUNNING
        self.state_svc.save(task)
        await self.executor_svc.execute_task_tree(task)

        # 6. Result Synthesis & Finalization
        has_failures = any(st.status == TaskStatus.ERROR for st in task.subtasks)
        task.status = TaskStatus.ERROR if has_failures else TaskStatus.COMPLETED
        task.report = self.synthesizer.synthesize(task)
        
        if task.status == TaskStatus.COMPLETED:
            self.affective.adjust_state("goal_reached", magnitude=0.2)
        else:
            self.affective.adjust_state("error", magnitude=0.25)
        
        # 7. Delegated Reflection (ReflectionEngine)
        await self.reflection_svc.reflect_on_task(task)
        return task



    async def trigger_self_evolution(self):
        try:
            from packages.orchestration.agi.cognitive.goal_synthesizer import GoalSynthesizer
            synthesizer = GoalSynthesizer(model_orch=self.model_orch)
            asyncio.create_task(synthesizer.run_synthesis_cycle())
            from packages.orchestration.agi.learning.memory_distiller import memory_distiller
            asyncio.create_task(memory_distiller.run_distillation_cycle())
        except Exception as e: _log.error(f"Evolution failed: {e}")

    async def shutdown(self):
        async with self._lock:
            if not self._is_running: return
            try: await self.watchdog.stop()
            except: pass
            self._is_running = False

    async def _update_project_context(self, project_id: str, context: dict):
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository
        async with AsyncSessionLocal() as db:
            await ProjectRepository.update_fields(db, project_id, execution_context=context)
            await db.commit()

# --- Singleton ---
sovereign_cortex = SovereignCortex()
def get_sovereign_cortex() -> SovereignCortex: return sovereign_cortex
nexus_orchestrator = sovereign_cortex
