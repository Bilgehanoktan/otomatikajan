"""
Sovereign Cortex — Phase 33 (Egemelik ve Öz-Yönetişim)
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

from agents.agent_registry import build_agents
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from memory.retrieval import context_builder
from quality.output_schema import output_parser, AgentOutput
from packages.orchestration.agi.task_governance import SovereignGoal, GovernedTask, GovernanceStatus, TaskPlanner, TaskStateService, ReportSynthesizer, TaskStatus, ProjectTask, SubTask
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

_log = get_logger("agi_sovereign_cortex")

class SovereignCortex:
    """
    AGI'nin egemen bilişsel yönetim merkezi.
    İleri düzey öngörü, otonom planlama ve hafıza yönetişimi sağlar.
    """
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
        self.ws_manager = None # Set by API layer (WS Endpoint)
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
            
            # Provenance Memory Sync (Faz 12.1)
            await self._sync_provenance_memory()
            
            # Self-Update Capability Activation (Phase 33)
            self.load_self_updater()
            
            # Governance Watchdog Activation (Phase 41)
            await self.watchdog.start()

            # Metacognitive Drift Loop Activation (Phase 69)
            asyncio.create_task(self._metacognitive_drift_loop())
            
            _log.info(f"[SOVEREIGN] Bilişsel yönetim merkezi aktif. {len(self._agents)} ajan hazır.")

    def get_health(self) -> dict[str, float]:
        """Heal Engine ve Monitoring için sağlık skorları."""
        return self._health.copy()

    def agent_count(self) -> int:
        return len(self._agents) if self._agents else 0

    async def _metacognitive_drift_loop(self):
        """
        AGI Öz-Bakım Döngüsü (Phase 69).
        Bilişsel puanları kontrol eder ve gerekirse otonom refaktör tetikler.
        """
        while self._is_running:
            try:
                _log.info("[SOVEREIGN-AUTOCHECK] Bilişsel sağlık denetimi başlatılıyor...")
                report = await eval_harness.run_full_evaluation()
                score = report.get("overall_cognitive_score", 0.0)
                
                if score < 0.8:
                    _log.warning(f"[SOVEREIGN-AUTOCHECK] DÜŞÜK BİLİŞSEL PUAN: {score:.2f}. Otonom recalibration tetikleniyor.")
                    # Faz 69: Otonom iyileştirme
                    await self.architect.recalibrate_reasoning(report)
                else:
                    _log.info(f"[SOVEREIGN-AUTOCHECK] Bilişsel sağlık stabil: {score:.2f}")

                # Her 1 saatte bir kontrol et (Test için bu süreyi kısaltabiliriz)
                await asyncio.sleep(3600)
            except Exception as e:
                _log.error(f"[SOVEREIGN-AUTOCHECK] Öz-bakım döngüsü hatası: {e}")
                await asyncio.sleep(300)

    async def _ensure_specialist_availability(self, subtask: SubTask):
        """Eğer subtask çok özelleşmişse, otonom olarak bir uzman 'forge' eder."""
        role = subtask.agent_id
        if role not in self._agents:
            _log.info(f"[SOVEREIGN-WEAVER] Uzman ajan eksikliği saptandı: {role}. Otonom forgery başlatılıyor...")
            
            # Architect ile uzmanlık promptu oluştur
            specialist_prompt = await self.architect.forge_specialist_prompt(role, subtask.title + " " + subtask.description)
            
            from agents.agent_registry import Agent
            new_agent = Agent(
                id=role,
                name=f"{role.capitalize()} Specialist",
                emoji="🧩",
                role=f"Specialized {role}",
                system_prompt=specialist_prompt
            )
            new_agent.llm = self.model_orch
            
            # Runtime registry'e ekle
            self._agents[role] = new_agent
            self._health[role] = 1.0
            _log.info(f"[SOVEREIGN-WEAVER] Yeni uzman ajan sisteme dahil edildi: {role}")

    def load_self_updater(self):
        try:
            from packages.orchestration.application.self_updater import SelfUpdater
            self.self_updater = SelfUpdater(model_orch=self.model_orch)
        except Exception as e:
            _log.error(f"SelfUpdater load failed: {e}")

    async def coordinate_goal(
        self, 
        title: str, 
        description: str, 
        project_id: str = None,
        workflow_template: str = None,
        quality_profile: str = None,
        acceptance_criteria: str = None,
        execution_context: Dict[str, Any] = None
    ) -> ProjectTask:
        """
        Bir hedefi (Goal) koordine eder. Bu süreç sadece bir liste değil, 
        bir "Problem Frame" (Sorun Çerçevesi) oluşturma sürecidir.
        """
        if not self._is_running: await self.start()
        
        task_id = project_id or str(uuid.uuid4())
        _log.info(f"[SOVEREIGN] Hedef koordinasyonu başlatıldı: {title} ({task_id})")

        # Faz 45: Veritabanından mevcut projeyi yükle veya yeni oluştur
        from db.session import AsyncSessionLocal
        from db.repository import ProjectRepository
        from db.models import ProjectStatus
        
        async with AsyncSessionLocal() as db:
            existing = await ProjectRepository.get(db, task_id)
            if existing:
                _log.info(f"[SOVEREIGN-RESUME] Mevcut proje bulundu: {existing.title} ({task_id})")
                task = ProjectTask(id=existing.id, title=existing.title)
                # Durum ve context yükle
                task.status = TaskStatus.RUNNING if existing.status == ProjectStatus.QUEUED else TaskStatus.RESUMING
                task.description = existing.description or description
                task.execution_context = existing.execution_context or {}
                # Eğer alt görevler varsa onları da yüklemek gerekir (Basitleştirilmiş)
            else:
                task = ProjectTask(id=task_id, title=title)
                task.description = description
        task.workflow_template = workflow_template or "default"
        task.quality_profile = quality_profile or "standard"
        if acceptance_criteria:
            task.acceptance_criteria = acceptance_criteria if isinstance(acceptance_criteria, list) else [acceptance_criteria]
        if execution_context:
            task.execution_context.update(execution_context)

        # Phase 59: Metabolic Dreaming (Cognitive Compaction)
        # Eğer enerji düşükse (ECO), planlamaya geçmeden önce 'Rüya Döngüsü' ile hafızayı optimize et.
        if affective_core.energy < 0.3:
            _log.info(f"[SOVEREIGN-DREAM] Düşük enerji tespiti ({affective_core.energy:.2f}). Bilişsel Sıkıştırma başlatılıyor...")
            from db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await memory_pruner.dream_cycle(db)

        # --- Phase 55: Otonom Güvenlik ve Etik Denetimi (Guardrail) ---
        m_safety = metabolic_governor.check_safety()
        audit = await axiology_engine.evaluate_alignment(
            target={"title": title, "description": description}, 
            context="initial_goal",
            metabolic_status=m_safety
        )
        
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

        # Faz 20 & 42: Bilişsel Ketleme Destekli Planlama
        subtasks = await self.planner.plan_sovereign(title, description)
        
        # Faz 65: Öz-Yansıma ve Plan Denetimi (Reflective Reasoning Loop)
        _log.info("[SOVEREIGN] Plan öz-yansıma döngüsü başlatılıyor (Faz 65)...")
        
        MAX_REVISIONS = 2
        for revision_step in range(MAX_REVISIONS + 1):
            # Denetim için alt görevleri JSON formatına çevir
            plan_summary = [{"agent_id": st.agent_id, "prompt": st.prompt} for st in subtasks]
            audit_res = await metacognitive_auditor.audit_plan(title, plan_summary)
            
            is_safe = audit_res.get("is_safe", True)
            coverage = audit_res.get("coverage_score", 1.0)
            
            if not is_safe or coverage < 0.7:
                if revision_step < MAX_REVISIONS:
                    _log.warning(f"[SOVEREIGN-REFLECT] Plan yetersiz bulundu ({'GÜVENSİZ' if not is_safe else 'Eksik Kapsam: '+str(coverage)}). Revize ediliyor (Deneme {revision_step+1}/{MAX_REVISIONS})...")
                    # Geri bildirimi topla ve yeniden planla
                    revision_context = f"\n\n[MİMARİ DENETİM GERİ BİLDİRİMİ]: {audit_res.get('refinement_suggestion')}\nEksikler: {', '.join(audit_res.get('gaps', []))}"
                    subtasks = await self.planner.plan_sovereign(title, description + revision_context)
                else:
                    _log.error(f"[SOVEREIGN-REFLECT] Plan {MAX_REVISIONS} denemede mükemmelleştirilemedi. Kritik hata: {audit_res.get('refinement_suggestion')}")
                    # En iyi planla devam et veya hata fırlat (AGI otonomisi gereği en iyisiyle devam etmeyi seçebilir)
                    break
            else:
                _log.info(f"[SOVEREIGN-REFLECT] Plan onaylandı (Deneme: {revision_step}, Logic: {audit_res.get('logic_score')}, Coverage: {coverage})")
                break
        
        # --- Faz 20 & 12.1: Stratejik ve Bilişsel Bağlam Entegrasyonu ---
        strategic_context = await memory_api.get_strategic_context(query=f"{title} {description}")
        cognitive_memory = await self._sync_provenance_memory() # Faz 12.1: Otonom hafıza
        
        # --- Phase 33: Bilişsel Öngörü (Foresight Simulation) ---
        _log.info("[SOVEREIGN] Paralel gelecekler (futures) simüle ediliyor...")
        timelines = await foresight_cortex.simulate_parallel_futures({"title": title, "content": description})
        optimal = await foresight_cortex.select_optimal_timeline(timelines)
        if optimal:
            _log.info(f"[SOVEREIGN] Optimum zaman çizgisi seçildi: {optimal.get('timeline_name')} (Risk Skoru: {optimal.get('risk_score')})")
            description += f"\n\n[STRATEJİK YÖNLENDİRME]: {optimal.get('potential_outcome')}"

        # --- Faz 28: Duygusal Durum Kalibrasyonu ---
        frame = ProblemFrame(task_type=TaskType.OPERATION, objective=title, risk_level=RiskLevel.MEDIUM)
        # Bilişsel hafızadan son bölümleri çek
        recent_episodes = await synaptic_cortex.search(db=None, query="", category="episode_record", top_k=5)
        # None DB bypass (UGC Hot Cache retrieval)
        aff_state = await self.motivation.recalibrate_state(recent_episodes, frame)
        
        _log.info(f"[SOVEREIGN] Motivasyon kalibre edildi. Politika: {aff_state.persistence_policy}")
        
        # Faz 45: Otonom Kurtarma ve Kısıtlama Entegrasyonu
        recovery_hint = task.execution_context.get("recovery_context")
        inhibition = task.execution_context.get("inhibition_signal")
        
        if recovery_hint:
            _log.info(f"[SOVEREIGN-RECOVERY] Kurtarma bağlamı enjekte ediliyor: {recovery_hint[:50]}...")
            description += f"\n\n### OTONOM KURTARMA BAĞLAMI:\n{recovery_hint}"
        
        if inhibition:
            _log.info(f"[SOVEREIGN-RECOVERY] Mimari kısıtlama (Inhibition) enjekte ediliyor: {inhibition[:50]}...")
            description += f"\n\n### KRİTİK KISITLAMA (NEGATİF SİNAPS):\n{inhibition}"

        # --- Phase 61: Grounded Planning (Failure Recall) ---
        try:
            _log.info("[SOVEREIGN-GROUNDING] Geçmiş başarısızlıklar ve dersler hatırlanıyor (Deep Recall + Causal V5)...")
            async with AsyncSessionLocal() as db:
                failures = await synaptic_cortex.search_with_causal_anchoring(
                    db=db, 
                    query=f"{title} {description}", 
                    top_k=5
                )
            # Filter for lessons/failures if needed, but causal search might bring related episodes too
            
            if failures:
                failure_context = "\n".join([f"- {f.get('body')}" for f in failures])
                description += f"\n\n### GEÇMİŞTEN DERSLER (BİLİŞSEL TEMELLENDİRME):\n{failure_context}"
                _log.info(f"[SOVEREIGN-GROUNDING] {len(failures)} ders planlamaya enjekte edildi.")
            else:
                _log.info("[SOVEREIGN-GROUNDING] Benzer bir geçmiş başarısızlık bulunamadı (Temiz sayfa).")
        except Exception as e:
            _log.warning(f"Failure recall failed: {e}")

        # --- Phase 61: Recursive Risk Detection (Auto-High-Risk & Blacklist) ---
        import re
        sensitive_patterns = [
            r"\.env", r"db/", r"core/agi/", r"main\.py"
        ]
        critical_blacklist = [
            r"rm\s+-rf", r"\bdrop\b\s+(table|database|schema)", 
            r"\btruncate\b\s+table", r"chmod\s+-?[R]?\s*777",
            r"(?i)select\s+.*\s+from\s+users(?!\s+where)", r">\s*(/dev/null|/etc/passwd)"
        ]
        
        combined_text = title.lower() + " " + description.lower()
        
        # 1. Kritik Blacklist (Anında Red)
        if any(re.search(pattern, combined_text) for pattern in critical_blacklist):
            _log.error(f"[SOVEREIGN-SAFETY] SİSTEMİ TEHLİKEYE ATACAK KRİTİK İHLAL ENGELLENDİ: '{title}'")
            task.status = TaskStatus.ERROR
            task.report = "⚠️ GÜVENLİK İHLALİ BAŞLATILAMADI: Sistem güvenliğini doğrudan tehdit eden kara listeye alınmış bir desen (rm -rf, drop table, chmod 777 vb.) tespit edildi."
            async with AsyncSessionLocal() as db:
                await ProjectRepository.update_fields(db, task.id, status=ProjectStatus.ERROR, error_detail=task.report)
                await db.commit()
            return task

        # 2. Risk (Konsensüs Gerektirenler)
        is_risky = any(re.search(pattern, combined_text) for pattern in sensitive_patterns)
        if is_risky:
            _log.warning(f"[SOVEREIGN-SAFETY] YÜKSEK RİSK TESPİT EDİLDİ: '{title}'. Konsensüs zorunlu kılınıyor.")
            # task execution_context'e risk sinyalini işle
            task.execution_context["consensus_required"] = True
            task.risk_level = "high"

        # Bilişsel Bağlamı Birleştir (Diyalektik planlama için gerekli)
        mood = self.affective.get_current_mood()
        
        # Katman 9: WorldModel Insights
        from packages.orchestration.agi.world import service_graph, task_state_graph
        service_health = service_graph.get_summary()
        failure_patterns = task_state_graph.get_summary()
        
        full_context = (
            f"{title}\nSTRATEJİK: {strategic_context}\n"
            f"BİLİŞSEL HAFIZA: {cognitive_memory}\n"
            f"WORLD_MODEL_HEALTH: {service_health}\n"
            f"FAILURE_PATTERNS: {failure_patterns}\n"
            f"MOOD: {mood}"
        )
        
        from dataclasses import asdict
        subtasks = await self._execute_dialectic_planning(task_id, title, full_context, description, asdict(aff_state))
        task.subtasks = subtasks
        
        # Priority #6 & #8: Architectural Audit Gate
        is_architectural = any(word in task.title.lower() or word in description.lower() 
                               for word in ["mimari", "architecture", "core", "refactor", "security"])
        if is_architectural:
            _log.info(f"[SOVEREIGN] Mimari Denetim (Audit Gate) başlatılıyor: {title}")
            from packages.orchestration.agi.security.audit_gate import audit_gate
            # Basit bir proposal objesi oluştur (Gerçekte daha zengin olabilir)
            proposal = {"title": title, "reasoning": description, "actions": []}
            is_safe = await audit_gate.verify_architecture_proposal(proposal)
            
            if not is_safe:
                _log.error(f"[SOVEREIGN] MİMARİ DENETİM REDDİ! Görev durduruluyor: {title}")
                task.status = TaskStatus.ERROR
                task.report = "GÜVENLİK/MİMARİ DENETİM REDDİ: Plan riskli bulundu."
                self.state_svc.save(task)
                return task

        # Faz 28: Motivasyon ve Durum Kalibrasyonu Devam
        task.status = TaskStatus.RUNNING
        self.state_svc.save(task)

        # --- Phase 37: Long-Horizon Persistence ---
        ctx = getattr(task, "execution_context", {}) or {}
        
        # DAG tabanlı ama Konsensüs odaklı yürütme
        events = {st.id: asyncio.Event() for st in task.subtasks}
        
        await asyncio.gather(*[self._process_node_recursive(st, task, events) for st in task.subtasks])
        
        has_failures = any(st.status == TaskStatus.ERROR for st in task.subtasks)
        
        # Faz 46: Otonom Görev Kurtarma (Resilience Recovery)
        if has_failures:
            _log.warning(f"[RECOVERY] Bazı alt görevler başarısız oldu. Kurtarma denemesi başlatılıyor...")
            failed_steps = [st for st in task.subtasks if st.status == TaskStatus.ERROR]
            remaining_steps = [st for st in task.subtasks if st.status == TaskStatus.PENDING]
            
            # Hata bağlamını oluştur
            error_context = "\n".join([f"- {st.agent_id}: {st.result[:200]}" for st in failed_steps])
            
            # Decomposer'dan tamir planı iste
            repair_prompt = f"""
            Şu adımlar BAŞARISIZ oldu:
            {error_context}
            
            Kalan hedefleri başarmak için alternatif bir plan oluştur. 
            Hatalı adımlardan kaçın veya farklı bir strateji (agent) belirle.
            """
            # Faz 47: Unified AGI Decomposer (Kurtarma Planı)
            new_subtasks = await agi_goal_decomposer.decompose(
                title=task.title, 
                description=repair_prompt, 
                available_agents=[], 
                affective_state=self.affective.get_state()
            )
            
            if new_subtasks:
                _log.info(f"[RECOVERY] Alternatif plan oluşturuldu ({len(new_subtasks)} adım). Yürütülüyor...")
                # Yeni subtaskları task listesine ekle
                task.subtasks.extend(new_subtasks)
                # Yeni adımlar için Event'leri güncelle
                for nst in new_subtasks:
                    if nst.id not in events:
                        events[nst.id] = asyncio.Event()
                
                # Sadece yeni adımları paralel yürüt (Bağımlılıklar Events üzerinden çözülür)
                await asyncio.gather(*[_process_node(nst) for nst in new_subtasks])
                
                # Tekrar kontrol et (Sadece aktif veya kurtarılamayan hataları baz al)
                has_failures = any(st.status == TaskStatus.ERROR for st in new_subtasks)

        task.status = TaskStatus.ERROR if has_failures else TaskStatus.COMPLETED
        task.report = self.synthesizer.synthesize(task)
        _log.info(f"[NEXUS] Hedef yürütme döngüsü tamamlandı. Durum: {task.status}")

        # Phase 28: Finale göre Duygusal tepki
        if task.status == TaskStatus.COMPLETED:
            self.affective.adjust_state("goal_reached", magnitude=0.2)
            # Phase 53: Positive Skill Synthesis
            try:
                from packages.orchestration.agi.cognitive.metacognitive_auditor import metacognitive_auditor
                # Fire and forget or awaited? Awaited for now to ensure DB session consistency.
                async with get_db() as db:
                    await metacognitive_auditor.distill_positive_skill(db, task.title, task.subtasks)
            except Exception as e:
                _log.warning(f"[SOVEREIGN-LEARNING] Pozitif öğrenme hatası: {e}")
        else:
            self.affective.adjust_state("error", magnitude=0.25)
        
        # --- Faz 27: Bilişsel Yansıma (Metacognition) ---
        await self._post_task_reflection(task)
        
        return task

    async def _execute_recursive_layer(self, children: List[SubTask], parent_task: ProjectTask, depth: int = 1):
        """Faz 51: Alt görev ağacını derinlemesine (recursive) yürütür."""
        events = {st.id: asyncio.Event() for st in children}
        await asyncio.gather(*[self._process_node_recursive(st, parent_task, events, depth) for st in children])

    async def _process_node_recursive(self, st: SubTask, task: ProjectTask, events: Dict[str, asyncio.Event], depth: int = 0):
        """Standardize node processing with recursion support."""
        # 1. Bağımlılıkları bekle
        dependencies = getattr(st, "dependencies", [])
        for dep_id in dependencies:
            if dep_id in events:
                await events[dep_id].wait()
        
        # --- Phase 37/51: Resume & Safety Check ---
        if st.status == TaskStatus.COMPLETED:
            events[st.id].set()
            return

        # 2. Bilişsel Yürütme (Rekürsif Kontrol - Faz 51)
        # Limit recursion depth to prevent infinite loops (Sovereign Safety)
        max_depth = 3
        if getattr(st, "is_complex", False) and depth < max_depth:
            m_safety = metabolic_governor.check_safety()
            if m_safety["can_expand"]:
                _log.info(f"[RECURSION] Derinleştirme aktif (Depth: {depth}): {st.id}")
                
                from agents.agent_registry import build_agents, discover_and_build_specialists
                all_agents = {**build_agents(), **discover_and_build_specialists()}
                agents_list = [{"id": aid, "role": a.role, "name": a.name} for aid, a in all_agents.items()]
                
                child_tasks = await agi_goal_decomposer.decompose(
                    title=f"Recursive Expansion of {st.id}",
                    description=st.prompt,
                    available_agents=agents_list,
                    affective_state=self.affective.get_state_matrix()
                )
                
                if child_tasks:
                    await self._execute_recursive_layer(child_tasks, task, depth + 1)
                    st.status = TaskStatus.COMPLETED
                    st.result = f"RECURSIVE-PATH: {len(child_tasks)} alt adım tamamlandı."
                    events[st.id].set()
                    return

        # 3. Nexus Yürütme (Leaf Node or Blocked Recursion)
        await self._execute_subtask_nexus(st, task)
        
        # --- Phase 60: Autonomous Evaluator (AEBC) ---
        # Adım tamamlandıktan sonra fiziksel/mantıksal kanıt denetimi yap.
        if st.status == TaskStatus.COMPLETED:
            eval_report = await sovereign_evaluator.evaluate_task_outcome(st)
            if not eval_report["is_grounded"]:
                _log.warning(f"[SOVEREIGN-DISSONANCE] Bilişsel Çelişki! {st.agent_id} başarılı dedi ama kanıt yok. ({eval_report['score']:.2f})")
                # Eğer skor çok düşükse (Hallüsinasyon şüphesi), durumu ERROR'a çek ve bir kez otomatik retry dene.
                if eval_report["score"] < 0.5 and getattr(st, "attempts", 0) < 1:
                    _log.info(f"[SOVEREIGN-RECORRECTION] Otonom Öz-Düzeltme başlatılıyor: {st.id}")
                    st.status = TaskStatus.ERROR
                    st.result = f"BİLİŞSEL ÇELİŞKİ HATASI: {eval_report['missing']}. Lütfen gerçek kanıt (dosya vb.) oluşturun."
                    st.attempts = getattr(st, "attempts", 0) + 1
                    # Recursive retry (Wait one metabolic cycle)
                    await asyncio.sleep(2)
                    return await self._process_node_recursive(st, task, events, depth)
                else:
                    # Kısmi başarı olarak işaretle veya uyarı ile devam et
                    st.result += f"\n[WARNING: LOW_GROUNDING_EVIDENCE ({eval_report['score']:.2f})]"
        
        # --- Update Persistence Context ---
        ctx = getattr(self, "execution_context", {})
        progress = ctx.get("agi_progress", [])
        if st.agent_id not in progress:
            progress.append(st.agent_id)
        ctx["agi_progress"] = progress
        await self._update_project_context(task.id, ctx)
        
        events[st.id].set()

    async def _execute_dialectic_planning(self, task_id: str, title: str, context: str, description: str, affective_state: Optional[Dict[str, float]] = None) -> list[SubTask]:
        """Birden fazla ajanın tartışıp konsensüse vardığı üst düzey planlama."""
        from agents.agent_registry import build_agents
        
        _log.info(f"[DIALECTIC] Dinamik planlama ve dekompozisyon başlatılıyor: {title}")
        
        # 1. Mevcut ajan listesini al
        from agents.agent_registry import build_agents, discover_and_build_specialists
        all_agents = build_agents()
        all_agents.update(discover_and_build_specialists())
        
        available_agents = [{"id": a.id, "name": a.name, "role": a.role_name} for a in all_agents.values()]
        
        # Faz 45: Specialized DeerFlow Agent Selection
        target_role = "architect"
        if "research" in title.lower() or "research" in description.lower():
            target_role = "deerflow_researcher"
        elif "plan" in title.lower() or "decompose" in description.lower():
            target_role = "deerflow_planner"
        elif "review" in title.lower() or "audit" in description.lower():
            target_role = "deerflow_reviewer"
            
        _log.info(f"[DIALECTIC] Hedef rol uzmanı seçildi: {target_role}")

        # --- Phase 37: Long-Horizon Persistence Loading ---
        # Note: Assuming self.current_task is accessible or passed via context
        ctx = getattr(self, "execution_context", {})
        if ctx.get("agi_subtasks"):
            _log.info(f"[RESUME] Proje {task_id} için mevcut plan yükleniyor.")
            from packages.orchestration.agi.task_governance import SubTask
            subtasks = [SubTask(**st_data) for st_data in ctx["agi_subtasks"]]
            # Start from index if provided
            start_index = ctx.get("agi_current_index", 0)
        else:
            # 2. Dinamik olarak planı dekompoze et (Affective Coupling Aktif)
            # Faz 45: target_role (Specialist) artık dekompozisyona liderlik ediyor.
            subtasks = await agi_goal_decomposer.decompose(title, description, available_agents, affective_state, lead_agent_role=target_role)
            start_index = 0

        
        # --- Phase 43: Öngörülü Yönetişim (Shadow Audit) ---
        _log.info(f"[SOVEREIGN] Gölge Denetim (Shadow Audit) başlatılıyor: {len(subtasks)} alt görev kontrol ediliyor.")
        predicted_violations = await self.watchdog.predict_violations(subtasks)
        
        if predicted_violations:
            _log.warning(f"[SOVEREIGN] Planlama aşamasında {len(predicted_violations)} İHLAL ÖNGÖRÜLDÜ! Re-planning tetikleniyor.")
            
            # İhlalleri Bilişsel Hafızaya Ketleme (Inhibition) olarak kaydet
            try:
                from db.session import get_db
                async with get_db() as db:
                    for v in predicted_violations:
                        await synaptic_cortex.save_architectural_inhibition(
                            db=db,
                            rule_id=v.rule_id,
                            target=v.target,
                            description=f"[PREDICTION] {v.description}"
                        )
            except Exception as e:
                _log.error(f"Prediction saving failed: {e}")
                
            # Takviyeli Planlama ile yeniden planla (Sovereign Planner artık inhibisyonları biliyor)
            _log.info("[SOVEREIGN] Takviyeli Planlayıcı (Reinforced Planner) ile yeniden kurgulanıyor...")
            # Faz 45: Tarihçe (context) aktarımı
            subtasks = await self.planner.plan_sovereign(title, description, history=context)
            
        # Fallback: Eğer hala plan yoksa statik planner'ı kullan
        if not subtasks:
            _log.warning("[DIALECTIC] Dinamik plan boş döndü. Statik planner fallback devrede.")
            subtasks = self.planner.plan(title, description)
        
        _log.info(f"[DIALECTIC] Plan oluşturuldu. Alt görev sayısı: {len(subtasks)}")
        return subtasks

    async def _post_task_reflection(self, task: ProjectTask):
        """Görev sonrası otonom öğrenme ve yansıma döngüsü."""
        def _deep_convert_enums(obj):
            if isinstance(obj, dict):
                return {k: _deep_convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_deep_convert_enums(v) for v in obj]
            elif hasattr(obj, "value"): # Enum check
                return obj.value
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        try:
            _log.info(f"[NEXUS] Bilişsel yansıma döngüsü tetiklendi: {task.id}")
            
            # 1. Episode kaydını inşa et
            episode = EpisodeRecord(
                episode_id=task.id,
                problem_frame=ProblemFrame(
                    task_type=TaskType.OPERATION, # Default
                    objective=task.title,
                    risk_level=RiskLevel.MEDIUM
                ),
                final_output=task.report
            )
            
            # Alt görev sonuçlarını ActionRecord olarak ekle
            for st in task.subtasks:
                episode.actions.append(ActionRecord(
                    step_id=st.id,
                    agent_id=st.agent_id, # Schema updated to include agent_id
                    tool_used="velocity_engine",
                    output_data=st.result,
                    success=(st.status == TaskStatus.COMPLETED),
                    duration_s=st.duration_s or 0.0
                ))
            
            # Doğrulama raporunu ekle
            episode.verification = VerificationReport(
                result_status=(task.status == TaskStatus.COMPLETED),
                evidence_summary=task.report[:1000] if task.report else "Kanıt yok",
                confidence_adjusted=0.8,
                integration_reality_score=0.9 if task.status == TaskStatus.COMPLETED else 0.4
            )

            # 2. Bilişsel Ayna ile analiz et
            reflected_episode = await cognitive_mirror.reflect(episode)
            
            # 3. Memory Gate: Hafıza Yazım Denetimi (Katman 7.7)
            is_eligible = await memory_gate.evaluate_eligibility(reflected_episode)
            if not is_eligible:
                _log.warning(f"[SOVEREIGN] Episode hafıza için uygun görülmedi: {task.id}")
                return

            # Faz 45: Bilişsel Devamlılık (Thought Thread) — Memory Gate'ten geçenler için
            thought_text = f"Görev '{task.title}' tamamlandı ({task.status}). Özet: {task.report[:100] if task.report else 'Özet yok'}..."
            try:
                from db.session import get_db
                async with get_db() as db:
                    await synaptic_cortex.save_thought_thread(db, thought_text, context_id="global")
            except Exception as e:
                _log.error(f"Thought thread save failed: {e}")

            # 4. Episode kaydını kalıcı hafızaya işle
            from db.session import get_db
            async with get_db() as db:
                ep_dict = _deep_convert_enums(asdict(reflected_episode))
                # Compatibility shim for older save_episode implementation
                ep_dict["project_id"] = task.id
                ep_dict["title"] = task.title
                ep_dict["status"] = task.status.value
                episode_mem = await synaptic_cortex.save_episode(db, ep_dict)

            # 4. Skill çıkarımı (Eğer uygunsa)
            if reflected_episode.verification and reflected_episode.verification.result_status:
                async with get_db() as db:
                    await skill_distiller.distill(reflected_episode, db)
            
            # 5. Hafızaya dersleri kaydet (Ekstra log olarak) — Memory V5: Parent ID Linkage
            async with get_db() as db:
                for lesson in reflected_episode.lessons_learned:
                    await synaptic_cortex.save(
                        db=db,
                        agent_id="system",
                        body=lesson,
                        category="cognitive_lesson",
                        project_id=task.id,
                        importance=0.6,
                        metadata={"task_status": task.status.value},
                        parent_id=episode_mem.id # CAUSAL ANCHORING
                    )

            # Faz 53: Bilgelik Döngüsü (Wisdom Loop) 
            # Tamamlanan görevden stratejik 'İçgüdüler' sentezle
            asyncio.create_task(wisdom_synthesizer.synthesize_from_task(task))

            _log.info(f"[NEXUS] Bilişsel yansıma tamamlandı. Çıkarılan ders sayısı: {len(reflected_episode.lessons_learned)}")
            
            # Faz 12.6: Metacognitive Health Check & Triggered Evolution
            if reflected_episode.metacognitive_score < 0.4:
                _log.warning(f"[SOVEREIGN] Düşük bilişsel skor ({reflected_episode.metacognitive_score})! Otonom evrim tetikleniyor.")
                await self.trigger_self_evolution()
            
            # Faz 37: Recursive Meta-Learning (Prompt Refinement)
            if not reflected_episode.verification.result_status:
                _log.info(f"[SOVEREIGN] Görev başarısız. Meta-Learning (Talimat İyileştirme) kontrol ediliyor.")
                for action in reflected_episode.actions:
                    if not action.success:
                        current_contract = self.planner.AGENT_CONTRACTS.get(action.agent_id)
                        if current_contract:
                            refined = await self.prompt_synth.refine_contract(
                                agent_id=action.agent_id,
                                failure_logs=reflected_episode.lessons_learned,
                                current_contract=current_contract
                            )
                            if refined:
                                # Faz 38: Kalite Kapısı (Quality Gate)
                                baseline_score = reflected_episode.metacognitive_score
                                if await self._verify_refinement_integrity(action.agent_id, refined, baseline_score):
                                    self.planner.update_contract(action.agent_id, refined)
                                    _log.info(f"[SOVEREIGN] '{action.agent_id}' için talimatlar meta-learning ile güncellendi.")
                                else:
                                    _log.warning(f"[SOVEREIGN] Bilişsel Gerileme Tespit Edildi! '{action.agent_id}' için iyileştirme REDDEDİLDİ.")
                                    # Gerekirse rollback (Daha önce iyileştirildiyse)
                                    self.planner.rollback_contract(action.agent_id)

        except Exception as e:
            _log.error(f"[NEXUS] Bilişsel yansıma hatası: {e}")
            import traceback
            _log.error(traceback.format_exc())

    async def _verify_refinement_integrity(self, agent_id: str, new_contract: dict, baseline: float) -> bool:
        """
        Faz 38: Yeni talimatların bilişsel düşüşe yol açmadığını doğrular.
        Simüle edilmiş bir görev çalıştırarak AGI Index'i kontrol eder.
        """
        _log.info(f"[SOVEREIGN] '{agent_id}' için otonom doğrulama (Harness Audit) başlatılıyor...")
        
        # 1. Mevcut planlayıcıyı geçici olarak güncelle
        old_contract = self.planner.dynamic_contracts.get(agent_id)
        self.planner.dynamic_contracts[agent_id] = new_contract
        
        # 2. Değerlendirme paketini çalıştır
        from packages.orchestration.agi.quality.sovereign_evaluator import sovereign_evaluator
        eval_report = await sovereign_evaluator.run_suite()
        new_score = eval_report["agi_index"]
        
        # 3. Eski geri al (Doğrulama aşamasında kalıcı olmasın)
        if old_contract:
            self.planner.dynamic_contracts[agent_id] = old_contract
        else:
            del self.planner.dynamic_contracts[agent_id]
            
        # Eğer AGI Index belirgin düşüş gösterirse (örn: 0.1 den fazla) reddet.
        # Basitlik için: new_score < baseline logic
        return new_score >= (baseline - 0.05)

    async def coordinate_architecture(self, proposal: Dict[str, Any]) -> bool:
        """
        Mimari bir öneriyi koordine eder: Denetim -> Scaffolding -> Görevlendirme.
        """
        from packages.orchestration.agi.security.audit_gate import AuditGate
        gate = AuditGate(self.model_orch)
        
        # 1. Mimari Denetim
        is_safe = await gate.verify_architecture_proposal(proposal)
        if not is_safe:
            _log.warning("[NEXUS] Mimari plan denetimi GEÇEMEDİ. İşlem iptal edildi.")
            return False
            
        # 2. Scaffolding (Yapısal İnşa)
        _log.info("[NEXUS] Mimari inşa (Scaffolding) başlatılıyor.")
        success = True
        for action in proposal.get("actions", []):
            if action["type"] == "create_subsystem":
                if not scaffolder.scaffold_subsystem(action):
                    success = False
            elif action["type"] == "split_file":
                if not scaffolder.split_file_structure(action["source"], action["targets"]):
                    success = False
                    
        if success:
            _log.info("[NEXUS] Mimari iskelet başarıyla inşa edildi.")
            # 3. İskeletlerin doldurulması (Implementation) için yeni proje başlatılabilir
            # Bu, CEO Engine veya Nexus tarafından otomatik koordine edilir.
            
        return success

    async def _execute_subtask_nexus(self, task: ProjectTask, subtask: SubTask):
        """
        [FAZ 72] Subtask'ın bilişsel hazırlığını yapar, hafıza enjeksiyonu gerçekleştirir 
        ve uygun ajana (Velocity Engine) gönderir.
        """
        try:
            # 1. Uzman Ajan Kontrolü
            await self._ensure_specialist_availability(subtask)

            # 2. Blackboard (Working Memory) Entegrasyonu
            blackboard = get_blackboard(task.id)
            working_ctx = await blackboard.get_working_context()
            
            # 3. SEMANTİK HAFIZA 2.0: Sinerjik Ders Enjeksiyonu (Phase 72)
            from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
            from db.session import AsyncSessionLocal
            
            _log.info(f"[SOVEREIGN-MEMORY] Ajan {subtask.agent_id} için sinerjik bellek taraması (V5.2) başlatılıyor...")
            try:
                async with AsyncSessionLocal() as db_mem:
                    # Görev bağlamına göre derin ve sinerjik hafıza taraması
                    past_lessons = await synaptic_cortex.search_with_causal_anchoring(
                        db=db_mem,
                        query=f"{subtask.title} {subtask.prompt}",
                        top_k=5,
                        use_synergy=True
                    )
                    
                    if past_lessons:
                        _log.info(f"[SOVEREIGN-MEMORY] {len(past_lessons)} sinerjik ders bulundu. Prompt'a enjekte ediliyor.")
                        
                        wisdom_block = "\n\n### 🧠 BİLİŞSEL MİRAS (SEMANTİK HAFIZA 2.0):\n"
                        wisdom_block += "Aşağıdaki geçmiş tecrübeler bu görev için kritik öneme sahiptir:\n"
                        for m in past_lessons:
                            wisdom_block += f"- {m.get('body')}\n"
                        
                        # Ajanın promptuna doğrudan enjekte et (Kaçınılmaz Bilgi)
                        subtask.prompt += wisdom_block
                        
                        # Blackboard'a kaydet
                        await blackboard.post_discovery("semantic_recall", f"Ajan {subtask.agent_id} için {len(past_lessons)} sinerjik tecrübe enjekte edildi.")
            except Exception as mem_err:
                _log.warning(f"[SOVEREIGN-MEMORY] Bellek enjeksiyon hatası: {mem_err}")

            # 4. Risk ve Simülasyon Kontrolü
            is_risky = any(kw in (subtask.prompt or "").lower() for kw in ["modify", "edit", "write", "delete", "create"])
            if is_risky or subtask.risk_level == RiskLevel.HIGH:
                _log.info(f"[SOVEREIGN-REFLECTION] Riskli görev tespiti: {subtask.title}. Foresight simülasyonu başlatılıyor...")
                sim_report = await foresight_cortex.simulate_plan(subtask)
                
                if sim_report.get("strategic_alignment_score", 0.0) < 0.6:
                    _log.warning("[SOVEREIGN-AUTO-REPAIR] Simülasyon başarısız. Revizyon gerekiyor.")
                    await self.replan_subtask(task, subtask, sim_report.get("reasoning", "Düşük stratejik uyum."))
                    return

            # 5. Yürütme Döngüsü (Attempt & Recovery)
            subtask.status = TaskStatus.RUNNING
            t_start = time.time()
            max_attempts = self.motivation.get_persistence_multiplier() or 2
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                try:
                    from packages.orchestration.agi.operational.velocity_engine import velocity_engine
                    
                    # Dinamik Context Hazırlığı
                    enriched_context = await context_builder.build_context(
                        agent_id=subtask.agent_id,
                        task_text=subtask.prompt,
                        project_id=task.id,
                        internal_monologue=getattr(subtask, 'internal_monologue', '')
                    )
                    
                    # 6. Yürütme (Velocity Engine)
                    result = await velocity_engine.simulate_and_execute(
                        agent_id=subtask.agent_id,
                        prompt=subtask.prompt,
                        context=enriched_context,
                        task_id=task.id
                    )
                    
                    if result.success:
                        subtask.status = TaskStatus.COMPLETED
                        subtask.result = str(result.output_data)
                        subtask.internal_monologue = result.reflection
                        
                        # 7. Çıktı Denetimi (Phase 67)
                        audit_res = await reflective_synthesizer.audit_subtask(subtask, task.to_frame())
                        if not audit_res.get("is_valid", False) and attempts < max_attempts:
                            _log.warning(f"[SOVEREIGN-AUDIT] Çıktı reddedildi. Yeniden deneme {attempts}/{max_attempts}...")
                            subtask.prompt += f"\n\n### ÖZ-ELEŞTİRİ VE DÜZELTME:\n{audit_res.get('repair_hint', 'Hata düzeltilmeli.')}"
                            continue
                        
                        _log.info(f"[SOVEREIGN-EXECUTE] Subtask başarıyla tamamlandı: {subtask.agent_id}")
                        break
                except Exception as ex:
                    _log.error(f"[SOVEREIGN-EXECUTE] Kritik yürütme hatası: {ex}")
                    if attempts >= max_attempts:
                        subtask.status = TaskStatus.ERROR
                        break
            
            subtask.duration_s = time.time() - t_start

        except Exception as e:
            # Phase 65: Failure Learning (Priority 5)
            await blackboard.post_warning(subtask.agent_id or "internal", f"Görev hatası: {str(e)}", severity="critical")
            raise e

    async def replan_subtask(self, task: GovernedTask, subtask: SubTask, critique: str):
        """
        Başarısız bir simülasyon sonrası alt görevi otonom olarak yeniden planlar.
        'Self-Correction' (Otonom Kendi Kendini Düzeltme) döngüsüdür.
        """
        _log.info(f"[SOVEREIGN-REPLAN] Görev revize ediliyor: {subtask.title}")
        
        prompt = f"""
        Aşağıdaki alt görev, simülasyon aşamasında başarısız oldu.
        NEDEN: {critique}
        
        ORİJİNAL GÖREV:
        - Başlık: {subtask.title}
        - Eylem: {subtask.action}
        - Hedef: {task.title}
        
        Lütfen bu görevi, yukarıdaki eleştiriyi dikkate alarak daha güvenli ve etkili bir şekilde yeniden yapılandır. 
        Sadece güncellenmiş görev talimatlarını döndür.
        """
        
        try:
            response = await self.architect.refactor_plan(prompt)
            # Alt görevi güncelle
            subtask.content = response
            subtask.status = TaskStatus.QUEUED # Tekrar sıraya al
            _log.info(f"[SOVEREIGN-REPLAN] Görev başarıyla revize edildi ve tekrar sıraya alındı.")
        except Exception as e:
            _log.error(f"[SOVEREIGN-REPLAN] Revizyon hatası: {e}")
            subtask.status = TaskStatus.ERROR

    async def _execute_subtask_core(self, task: GovernedTask, subtask: SubTask):
        """Orijinal alt görev yürütme mantığı (Refactor edilmiş)."""
        # ... (Önceki mantık devam eder)

    async def decompose_subtask(self, parent_goal: SovereignGoal, subtask: SubTask) -> bool:
        """
        Büyük bir alt görevi (SubTask) otonom olarak daha küçük parçalara böler.
        'Sovereign Depth' (Recursive AGI) çekirdek mantığıdır.
        """
        prompt = f"""
        Şu görev 'COMPLEX' olarak işaretlendi: {subtask.title}
        Görevi daha küçük, yönetilebilir 3-5 adet atomic alt-görev (Sub-SubTask) haline getir.
        
        KAPSAM: {subtask.content or subtask.prompt}
        HEDEF: {parent_goal.title}
        
        JSON Liste formatında döndür:
        [{{"title": "...", "assigned_agent": "...", "content": "..."}}]
        """
        try:
            response = await self.architect.decompose(prompt) # Architect'te yeni metod
            sub_tasks_data = json.loads(response)
            
            for i, data in enumerate(sub_tasks_data):
                new_st = SubTask(
                    id=f"{subtask.id}.{i+1}",
                    title=data["title"],
                    assigned_agent=data["assigned_agent"],
                    prompt=data["content"],
                    parent_id=subtask.id,
                    status=TaskStatus.QUEUED
                )
                parent_goal.subtasks.append(new_st)
            
            subtask.status = TaskStatus.COMPLETED # Ana görev 'Ayrıştırıldı' olarak işaretlenir.
            return True
        except Exception as e:
            _log.error(f"[SOVEREIGN-DEPTH] Ayrıştırma hatası: {e}")
            return False

        st.duration_s = time.time() - t_start

    async def _diagnostic_reflection(self, st: SubTask, errors: List[str]) -> str:
        """Hata durumunda 'neden' sorusunu soran mini-reflection."""
        prompt = f"""
        Şu alt görev başarısız oldu: {st.prompt}
        Hatalar: {'; '.join(errors)}
        
        Kritik Analiz:
        1. Hata sistemsel mi (bağlantı, dosya yok vb.) yoksa mantıksal mı (yanlış kod, yanlış akış)?
        2. Bir sonraki denemede strateji nasıl değişmeli? (Örn: "Dosyayı okumadan önce listele", "Doğru kütüphaneyi kontrol et")
        
        Lütfen ajana vereceğin kısa, net ve otonom bir tavsiye (actionable advice) üret.
        """
        try:
            response = await self.model_orch.complete_task(
                agent_role="critic",
                prompt=prompt,
                system_prompt="Sen bir 'Root Cause Analyst' birimisin. Ajanın başarısızlığını teknik olarak analiz et."
            )
            return response.content
        except Exception as e:
            _log.error(f"Diagnostic reflection failed: {e}")
            return "Önceki hataları incele ve daha dikkatli bir yaklaşım dene."

    async def _sync_provenance_memory(self):
        """Otonom değişim kayıtlarını hafızaya yükler."""
        try:
            from packages.orchestration.agi.cognitive.chronicler import chronicler
            history = await chronicler.get_recent_provenance(limit=10)
            if history:
                 summary = "; ".join([f"{h.get('target', 'sys')}: {h.get('reasoning', 'mod')[:50]}" for h in history])
                 _log.info(f"[NEXUS] Bilişsel hafıza senkronize edildi. (Kayıt sayısı: {len(history)})")
                 return summary
        except Exception as e:
            _log.warning(f"Cognitive sync failed: {e}")
        return ""

    async def trigger_self_evolution(self):
        """Otonom iyileştirme döngüsünü (GoalSynthesizer) manuel olarak tetikler."""
        try:
            from packages.orchestration.agi.cognitive.goal_synthesizer import GoalSynthesizer
            synthesizer = GoalSynthesizer(model_orch=self.model_orch)
            # Arka planda çalıştır (Task'ı bloklama)
            asyncio.create_task(synthesizer.run_synthesis_cycle())

            # Phase 73: Memory Distiller Entegrasyonu (Faz 86 Stabilizasyonu)
            from packages.orchestration.agi.learning.memory_distiller import memory_distiller
            asyncio.create_task(memory_distiller.run_distillation_cycle())
            
            _log.info("[SOVEREIGN] Self-Evolution and Memory Distillation cycles started in background.")
        except Exception as e:
            _log.error(f"Failed to trigger evolution/distillation: {e}")

    async def resume_goal(self, project_id: str):
        """Kesintiye uğrayan bir hedefi DB'den yükler ve devam ettirir."""
        _log.info(f"[SOVEREIGN-RESUME] Proje kurtarma başlatıldı: {project_id}")
        from db.session import AsyncSessionLocal
        from db.repository import ProjectRepository
        
        async with AsyncSessionLocal() as db:
            p = await ProjectRepository.get(db, project_id)
            if not p:
                _log.error(f"[SOVEREIGN-RESUME] Proje bulunamadı: {project_id}")
                return
            
            # coordinate_goal'u mevcut proje bilgileriyle çağır
            # coordinate_goal içerisindeki DB yükleme mantığı sayesinde kaldığı yerden devam edecek.
            await self.coordinate_goal(
                title=p.title,
                description=p.description,
                project_id=p.id,
                execution_context=p.execution_context
            )

    async def shutdown(self):
        """Bilişsel yönetim merkezini güvenli bir şekilde kapatır."""
        async with self._lock:
            if not self._is_running: return
            _log.info("[SOVEREIGN] Kapatma dizisi başlatıldı...")
            
            # Watchdog'u durdur
            try:
                await self.watchdog.stop()
            except Exception as e:
                _log.error(f"Watchdog stop failed: {e}")
            
            self._is_running = False
            _log.info("[SOVEREIGN] Kapatma tamamlandı.")

# --- Singleton ---
sovereign_cortex = SovereignCortex()

def get_sovereign_cortex() -> SovereignCortex:
    return sovereign_cortex

# Compatibility Aliases for Phase 17/12.1 refactor
nexus_orchestrator = sovereign_cortex
get_nexus_orchestrator = get_sovereign_cortex
