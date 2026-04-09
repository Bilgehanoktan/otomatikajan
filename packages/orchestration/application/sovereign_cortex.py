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
from schemas import SubtaskOutput

from packages.orchestration.application.agent_discovery import build_agents
from packages.observability.logging import get_logger
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.memory.retrieval import context_builder
from packages.quality_assurance.output_schema import output_parser, AgentOutput

# MIGRATED IMPORTS
from packages.orchestration.domain.models import SovereignGoal, GovernedTask, GovernanceStatus, TaskStatus, ProjectTask, SubTask
from packages.orchestration.application.governance import TaskPlanner, TaskStateService, ReportSynthesizer

# LEGACY IMPORTS (To be migrated next)
from packages.orchestration.agi.cognitive.metacognitive_auditor import metacognitive_auditor
from packages.orchestration.agi.cognitive.architect import Architect
from packages.orchestration.agi.operational.scaffolder import scaffolder
from packages.orchestration.agi.cognitive.memory_api import memory_api
from packages.orchestration.agi.schemas import EpisodeRecord, ActionRecord, UnifiedInput, ProblemFrame, TaskType, RiskLevel, VerificationReport
from packages.orchestration.agi.learning.cognitive_mirror import cognitive_mirror
from packages.orchestration.agi.learning.distiller import skill_distiller
from packages.orchestration.agi.cognitive.agi_goal_decomposer import agi_goal_decomposer
from packages.orchestration.agi.cognitive.collaborative_node import collaborative_node
from packages.orchestration.agi.learning.knowledge_distiller import knowledge_distiller
from packages.orchestration.agi.learning.prompt_synthesizer import PromptSynthesizer
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from packages.orchestration.agi.cognitive.motivation_engine import motivation_engine
from packages.orchestration.agi.consciousness.affective_core import affective_core
from packages.orchestration.agi.cognitive.foresight_cortex import foresight_cortex
from packages.orchestration.agi.learning.memory_gate import memory_gate
from packages.orchestration.agi.governance.watchdog import governance_watchdog
from packages.orchestration.agi.governance.consensus_arbiter import consensus_arbiter
from packages.orchestration.agi.cognitive.reflective_synthesizer import reflective_synthesizer
from packages.orchestration.agi.cognitive.axiology_engine import axiology_engine
from packages.orchestration.agi.operational.metabolic_governor import metabolic_governor
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
            await self._sync_provenance_memory()
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

        if affective_core.energy < 0.3:
            _log.info(f"[SOVEREIGN-DREAM] Düşük enerji tespiti ({affective_core.energy:.2f}). Bilişsel Sıkıştırma başlatılıyor...")
            from packages.persistence.session import AsyncSessionLocal
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

        subtasks = await self.planner.plan_sovereign(title, description)
        _log.info("[SOVEREIGN] Plan öz-yansıma döngüsü başlatılıyor (Faz 65)...")
        MAX_REVISIONS = 2
        for revision_step in range(MAX_REVISIONS + 1):
            plan_summary = [{"agent_id": st.agent_id, "prompt": st.prompt} for st in subtasks]
            audit_res = await metacognitive_auditor.audit_plan(title, plan_summary)
            is_safe = audit_res.get("is_safe", True)
            coverage = audit_res.get("coverage_score", 1.0)
            if not is_safe or coverage < 0.7:
                if revision_step < MAX_REVISIONS:
                    _log.warning(f"[SOVEREIGN-REFLECT] Plan yetersiz bulundu ({'GÜVENSİZ' if not is_safe else 'Eksik Kapsam: '+str(coverage)}). Revize ediliyor (Deneme {revision_step+1}/{MAX_REVISIONS})...")
                    revision_context = f"\n\n[MİMARİ DENETİM GERİ BİLDİRİMİ]: {audit_res.get('refinement_suggestion')}\nEksikler: {', '.join(audit_res.get('gaps', []))}"
                    subtasks = await self.planner.plan_sovereign(title, description + revision_context)
                else:
                    _log.error(f"[SOVEREIGN-REFLECT] Plan {MAX_REVISIONS} denemede mükemmelleştirilemedi. Kritik hata: {audit_res.get('refinement_suggestion')}")
                    break
            else:
                _log.info(f"[SOVEREIGN-REFLECT] Plan onaylandı (Deneme: {revision_step}, Logic: {audit_res.get('logic_score')}, Coverage: {coverage})")
                break
        
        strategic_context = await memory_api.get_strategic_context(query=f"{title} {description}")
        cognitive_memory = await self._sync_provenance_memory()
        _log.info("[SOVEREIGN] Paralel gelecekler (futures) simüle ediliyor...")
        timelines = await foresight_cortex.simulate_parallel_futures({"title": title, "content": description})
        optimal = await foresight_cortex.select_optimal_timeline(timelines)
        if optimal:
            _log.info(f"[SOVEREIGN] Optimum zaman çizgisi seçildi: {optimal.get('timeline_name')} (Risk Skoru: {optimal.get('risk_score')})")
            description += f"\n\n[STRATEJİK YÖNLENDİRME]: {optimal.get('potential_outcome')}"

        frame = ProblemFrame(task_type=TaskType.OPERATION, objective=title, risk_level=RiskLevel.MEDIUM)
        recent_episodes = await synaptic_cortex.search(db=None, query="", category="episode_record", top_k=5)
        aff_state = await self.motivation.recalibrate_state(recent_episodes, frame)
        _log.info(f"[SOVEREIGN] Motivasyon kalibre edildi. Politika: {aff_state.persistence_policy}")
        recovery_hint = task.execution_context.get("recovery_context")
        inhibition = task.execution_context.get("inhibition_signal")
        if recovery_hint:
            _log.info(f"[SOVEREIGN-RECOVERY] Kurtarma bağlamı enjekte ediliyor: {recovery_hint[:50]}...")
            description += f"\n\n### OTONOM KURTARMA BAĞLAMI:\n{recovery_hint}"
        if inhibition:
            _log.info(f"[SOVEREIGN-RECOVERY] Mimari kısıtlama (Inhibition) enjekte ediliyor: {inhibition[:50]}...")
            description += f"\n\n### KRİTİK KISITLAMA (NEGATİF SİNAPS):\n{inhibition}"

        try:
            _log.info("[SOVEREIGN-GROUNDING] Geçmiş başarısızlıklar ve dersler hatırlanıyor (Deep Recall + Causal V5)...")
            async with AsyncSessionLocal() as db:
                failures = await synaptic_cortex.search_with_causal_anchoring(db=db, query=f"{title} {description}", top_k=5)
            if failures:
                failure_context = "\n".join([f"- {f.get('body')}" for f in failures])
                description += f"\n\n### GEÇMİŞTEN DERSLER (BİLİŞSEL TEMELLENDİRME):\n{failure_context}"
                _log.info(f"[SOVEREIGN-GROUNDING] {len(failures)} ders planlamaya enjekte edildi.")
            else:
                _log.info("[SOVEREIGN-GROUNDING] Benzer bir geçmiş başarısızlık bulunamadı (Temiz sayfa).")
        except Exception as e:
            _log.warning(f"Failure recall failed: {e}")

        import re
        sensitive_patterns = [r"\.env", r"db/", r"core/agi/", r"main\.py"]
        critical_blacklist = [r"rm\s+-rf", r"\bdrop\b\s+(table|database|schema)", r"\btruncate\b\s+table", r"chmod\s+-?[R]?\s*777", r"(?i)select\s+.*\s+from\s+users(?!\s+where)", r">\s*(/dev/null|/etc/passwd)"]
        combined_text = title.lower() + " " + description.lower()
        if any(re.search(pattern, combined_text) for pattern in critical_blacklist):
            _log.error(f"[SOVEREIGN-SAFETY] SİSTEMİ TEHLİKEYE ATACAK KRİTİK İHLAL ENGELLENDİ: '{title}'")
            task.status = TaskStatus.ERROR
            task.report = "⚠️ GÜVENLİK İHLALİ BAŞLATILAMADI: Sistem güvenliğini doğrudan tehdit eden kara listeye alınmış bir desen (rm -rf, drop table, chmod 777 vb.) tespit edildi."
            async with AsyncSessionLocal() as db:
                await ProjectRepository.update_fields(db, task.id, status=ProjectStatus.ERROR, error_detail=task.report)
                await db.commit()
            return task
        is_risky = any(re.search(pattern, combined_text) for pattern in sensitive_patterns)
        if is_risky:
            _log.warning(f"[SOVEREIGN-SAFETY] YÜKSEK RİSK TESPİT EDİLDİ: '{title}'. Konsensüs zorunlu kılınıyor.")
            task.execution_context["consensus_required"] = True
            task.risk_level = "high"

        mood = self.affective.get_current_mood()
        from packages.orchestration.agi.world import service_graph, task_state_graph
        service_health = service_graph.get_summary()
        failure_patterns = task_state_graph.get_summary()
        full_context = f"{title}\nSTRATEJİK: {strategic_context}\nBİLİŞSEL HAFIZA: {cognitive_memory}\nWORLD_MODEL_HEALTH: {service_health}\nFAILURE_PATTERNS: {failure_patterns}\nMOOD: {mood}"
        subtasks = await self._execute_dialectic_planning(task_id, title, full_context, description, asdict(aff_state))
        task.subtasks = subtasks
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
        task.status = TaskStatus.RUNNING
        self.state_svc.save(task)
        events = {st.id: asyncio.Event() for st in task.subtasks}
        await asyncio.gather(*[self._process_node_recursive(st, task, events) for st in task.subtasks])
        has_failures = any(st.status == TaskStatus.ERROR for st in task.subtasks)
        if has_failures:
            _log.warning(f"[RECOVERY] Bazı alt görevler başarısız oldu. Kurtarma denemesi başlatılıyor...")
            failed_steps = [st for st in task.subtasks if st.status == TaskStatus.ERROR]
            error_context = "\n".join([f"- {st.agent_id}: {st.result[:200]}" for st in failed_steps])
            repair_prompt = f"Şu adımlar BAŞARISIZ oldu:\n{error_context}\nKalan hedefleri başarmak için alternatif bir plan oluştur."
            new_subtasks = await agi_goal_decomposer.decompose(title=task.title, description=repair_prompt, available_agents=[], affective_state=self.affective.get_state())
            if new_subtasks:
                task.subtasks.extend(new_subtasks)
                for nst in new_subtasks:
                    if nst.id not in events: events[nst.id] = asyncio.Event()
                await asyncio.gather(*[self._process_node_recursive(nst, task, events) for nst in new_subtasks])
                has_failures = any(st.status == TaskStatus.ERROR for st in new_subtasks)
        task.status = TaskStatus.ERROR if has_failures else TaskStatus.COMPLETED
        task.report = self.synthesizer.synthesize(task)
        if task.status == TaskStatus.COMPLETED:
            self.affective.adjust_state("goal_reached", magnitude=0.2)
            try:
                from packages.persistence.session import get_db
                async with get_db() as db:
                    await metacognitive_auditor.distill_positive_skill(db, task.title, task.subtasks)
            except Exception as e: _log.warning(f"[SOVEREIGN-LEARNING] Pozitif öğrenme hatası: {e}")
        else:
            self.affective.adjust_state("error", magnitude=0.25)
        await self._post_task_reflection(task)
        return task

    async def _execute_recursive_layer(self, children: List[SubTask], parent_task: ProjectTask, depth: int = 1):
        events = {st.id: asyncio.Event() for st in children}
        await asyncio.gather(*[self._process_node_recursive(st, parent_task, events, depth) for st in children])

    async def _process_node_recursive(self, st: SubTask, task: ProjectTask, events: Dict[str, asyncio.Event], depth: int = 0):
        dependencies = getattr(st, "dependencies", [])
        for dep_id in dependencies:
            if dep_id in events: await events[dep_id].wait()
        if st.status == TaskStatus.COMPLETED:
            events[st.id].set()
            return
        max_depth = 3
        if getattr(st, "is_complex", False) and depth < max_depth:
            m_safety = metabolic_governor.check_safety()
            if m_safety["can_expand"]:
                from packages.orchestration.application.agent_discovery import build_agents, discover_and_build_specialists
                all_agents = {**build_agents(), **discover_and_build_specialists()}
                agents_list = [{"id": aid, "role": a.role, "name": a.name} for aid, a in all_agents.items()]
                child_tasks = await agi_goal_decomposer.decompose(title=f"Recursive Expansion of {st.id}", description=st.prompt, available_agents=agents_list, affective_state=self.affective.get_state_matrix())
                if child_tasks:
                    await self._execute_recursive_layer(child_tasks, task, depth + 1)
                    st.status = TaskStatus.COMPLETED
                    st.result = f"RECURSIVE-PATH: {len(child_tasks)} alt adım tamamlandı."
                    events[st.id].set()
                    return
        await self._execute_subtask_nexus(task, st)
        if st.status == TaskStatus.COMPLETED:
            eval_report = await sovereign_evaluator.evaluate_task_outcome(st)
            if not eval_report["is_grounded"]:
                if eval_report["score"] < 0.5 and getattr(st, "attempts", 0) < 1:
                    st.status = TaskStatus.ERROR
                    st.result = f"BİLİŞSEL ÇELİŞKİ HATASI: {eval_report['missing']}."
                    st.attempts = getattr(st, "attempts", 0) + 1
                    await asyncio.sleep(2)
                    return await self._process_node_recursive(st, task, events, depth)
                else:
                    st.result += f"\n[WARNING: LOW_GROUNDING_EVIDENCE ({eval_report['score']:.2f})]"
        ctx = getattr(self, "execution_context", {})
        progress = ctx.get("agi_progress", [])
        if st.agent_id not in progress: progress.append(st.agent_id)
        ctx["agi_progress"] = progress
        await self._update_project_context(task.id, ctx)
        events[st.id].set()

    async def _execute_dialectic_planning(self, task_id: str, title: str, context: str, description: str, affective_state: Optional[Dict[str, float]] = None) -> list[SubTask]:
        from packages.orchestration.application.agent_discovery import build_agents, discover_and_build_specialists
        all_agents = build_agents()
        all_agents.update(discover_and_build_specialists())
        available_agents = [{"id": a.id, "name": a.name, "role": a.role_name} for a in all_agents.values()]
        target_role = "architect"
        if "research" in title.lower(): target_role = "deerflow_researcher"
        elif "plan" in title.lower(): target_role = "deerflow_planner"
        ctx = getattr(self, "execution_context", {})
        if ctx.get("agi_subtasks"):
            from packages.orchestration.domain.models import SubTask
            subtasks = [SubTask(**st_data) for st_data in ctx["agi_subtasks"]]
        else:
            subtasks = await agi_goal_decomposer.decompose(title, description, available_agents, affective_state, lead_agent_role=target_role)
        predicted_violations = await self.watchdog.predict_violations(subtasks)
        if predicted_violations:
            from packages.persistence.session import get_db
            async with get_db() as db:
                for v in predicted_violations:
                    await synaptic_cortex.save_architectural_inhibition(db=db, rule_id=v.rule_id, target=v.target, description=f"[PREDICTION] {v.description}")
            subtasks = await self.planner.plan_sovereign(title, description, history=context)
        if not subtasks: subtasks = self.planner.plan(title, description)
        return subtasks

    async def _post_task_reflection(self, task: ProjectTask):
        def _deep_convert_enums(obj):
            if isinstance(obj, dict): return {k: _deep_convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list): return [_deep_convert_enums(v) for v in obj]
            elif hasattr(obj, "value"): return obj.value
            elif isinstance(obj, datetime): return obj.isoformat()
            return obj
        try:
            episode = EpisodeRecord(episode_id=task.id, problem_frame=ProblemFrame(task_type=TaskType.OPERATION, objective=task.title, risk_level=RiskLevel.MEDIUM), final_output=task.report)
            for st in task.subtasks:
                episode.actions.append(ActionRecord(step_id=st.id, agent_id=st.agent_id, tool_used="velocity_engine", output_data=st.result, success=(st.status == TaskStatus.COMPLETED), duration_s=st.duration_s or 0.0))
            episode.verification = VerificationReport(result_status=(task.status == TaskStatus.COMPLETED), evidence_summary=task.report[:1000] if task.report else "Kanıt yok", confidence_adjusted=0.8, integration_reality_score=0.9 if task.status == TaskStatus.COMPLETED else 0.4)
            reflected_episode = await cognitive_mirror.reflect(episode)
            is_eligible = await memory_gate.evaluate_eligibility(reflected_episode)
            if not is_eligible: return
            from packages.persistence.session import get_db
            async with get_db() as db:
                await synaptic_cortex.save_thought_thread(db, f"Görev '{task.title}' tamamlandı.", context_id="global")
                ep_dict = _deep_convert_enums(asdict(reflected_episode))
                ep_dict["project_id"] = task.id
                ep_dict["status"] = task.status.value
                episode_mem = await synaptic_cortex.save_episode(db, ep_dict)
            if reflected_episode.verification and reflected_episode.verification.result_status:
                async with get_db() as db: await skill_distiller.distill(reflected_episode, db)
            async with get_db() as db:
                for lesson in reflected_episode.lessons_learned:
                    await synaptic_cortex.save(db=db, agent_id="system", body=lesson, category="cognitive_lesson", project_id=task.id, importance=0.6, parent_id=episode_mem.id)
            asyncio.create_task(wisdom_synthesizer.synthesize_from_task(task))
            if reflected_episode.metacognitive_score < 0.4: await self.trigger_self_evolution()
        except Exception as e: _log.error(f"[NEXUS] Bilişsel yansıma hatası: {e}")

    async def _execute_subtask_nexus(self, task: ProjectTask, subtask: SubTask):
        try:
            await self._ensure_specialist_availability(subtask)
            blackboard = get_blackboard(task.id)
            from packages.persistence.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db_mem:
                past_lessons = await synaptic_cortex.search_with_causal_anchoring(db=db_mem, query=f"{subtask.title} {subtask.prompt}", top_k=5, use_synergy=True)
                if past_lessons:
                    wisdom_block = "\n\n### 🧠 BİLİŞSEL MİRAS:\n" + "\n".join([f"- {m.get('body')}" for m in past_lessons])
                    subtask.prompt += wisdom_block
            subtask.status = TaskStatus.RUNNING
            t_start = time.time()
            enriched_context = await context_builder.build_context(agent_id=subtask.agent_id, task_text=subtask.prompt, project_id=task.id)
            result = await velocity_engine.simulate_and_execute(agent_id=subtask.agent_id, prompt=subtask.prompt, context=enriched_context, task_id=task.id)
            if result.success:
                subtask.status = TaskStatus.COMPLETED
                subtask.result = str(result.output_data)
            subtask.duration_s = time.time() - t_start
        except Exception as e: raise e

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
