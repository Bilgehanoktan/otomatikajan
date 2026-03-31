"""
Nexus Orchestrator — Faz 17 (Bilişsel Düğüm)
Düşünce -> Karar Konsensüsü -> Simülasyon -> Yürütme -> Özyinelemeli Öğrenme
"""

import asyncio
import uuid
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from agents.agent_registry import build_agents
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from memory.retrieval import context_builder
from quality.output_schema import output_parser, AgentOutput
from core.task_management import ProjectTask, SubTask, TaskStatus, TaskPlanner, TaskStateService, ReportSynthesizer
from core.agi.cognitive.architect import Architect
from core.agi.operational.scaffolder import scaffolder
from core.agi.cognitive.memory_api import memory_api

_log = get_logger("nexus_orchestrator")

class NexusOrchestrator:
    """
    AGI'nin merkezi bilişsel düğümü.
    Eski monolitik orkestratörden evrilerek, ajanlar arası konsensüs ve 
    niyet odaklı planlama yetenekleri kazanmıştır.
    """
    def __init__(self):
        self.model_orch  = ModelOrchestrator()
        self.planner     = TaskPlanner()
        self.state_svc   = TaskStateService()
        self.synthesizer = ReportSynthesizer()
        self.architect   = Architect(model_orch=self.model_orch)
        self.self_updater = None # Faz 8 Infra
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
            
            # Self-Updater başlat (Legacy Compatibility)
            try:
                from core.self_updater import SelfUpdater
                import os
                self.self_updater = SelfUpdater(
                    model_orch=self.model_orch,
                    project_root=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                )
                _log.info("[NEXUS] Self-Updater hazır.")
            except Exception as e:
                _log.warning(f"[NEXUS] Self-Updater başlatılamadı: {e}")

            _log.info(f"[NEXUS] Bilişsel düğüm aktif. {len(self._agents)} ajan hazır.")

    def get_health(self) -> dict[str, float]:
        """Heal Engine ve Monitoring için sağlık skorları."""
        return self._health.copy()

    def agent_count(self) -> int:
        return len(self._agents) if self._agents else 0

    def load_self_updater(self):
        try:
            from core.self_updater import SelfUpdater
            self.self_updater = SelfUpdater(model_orch=self.model_orch)
        except Exception as e:
            _log.error(f"SelfUpdater load failed: {e}")

    async def coordinate_goal(self, title: str, description: str, project_id: str = None) -> ProjectTask:
        """
        Bir hedefi (Goal) koordine eder. Bu süreç sadece bir liste değil, 
        bir "Problem Frame" (Sorun Çerçevesi) oluşturma sürecidir.
        """
        if not self._is_running: await self.start()
        
        task_id = project_id or str(uuid.uuid4())
        _log.info(f"[NEXUS] Hedef koordinasyonu başlatıldı: {title} ({task_id})")
        
        # --- Faz 20: Stratejik Bağlam Entegrasyonu ---
        strategic_context = await memory_api.get_strategic_context(query=f"{title} {description}")
        _log.info("[NEXUS] Stratejik hafıza bağlamı yüklendi.")
        
        task = ProjectTask(id=task_id, title=title)
        # Niyet Odaklı Dekompozisyon (Intent-Based Decomposition)
        # Plana stratejik bağlamı ekleyerek dekompozisyonu güçlendiriyoruz
        task.subtasks = self.planner.plan(f"{title}\nBAĞLAM: {strategic_context}", description)
        task.status = TaskStatus.RUNNING
        self.state_svc.save(task)

        # DAG tabanlı ama Konsensüs odaklı yürütme
        events = {st.agent_id: asyncio.Event() for st in task.subtasks}
        
        async def _process_node(st: SubTask):
            # 1. Bağımlılıkları bekle (Standard DAG)
            from core.legacy.orchestrator import DAG_WORKFLOW # Legacy uyumu korunarak aktarma
            dependencies = DAG_WORKFLOW.get(st.agent_id, [])
            for dep_id in dependencies:
                if dep_id in events:
                    await events[dep_id].wait()
            
            # 2. Bilişsel Yürütme (Aşama 17'ye özel)
            await self._execute_subtask_nexus(st, task)
            events[st.agent_id].set()

        await asyncio.gather(*[_process_node(st) for st in task.subtasks])
        
        has_failures = any(st.status == TaskStatus.FAILED for st in task.subtasks)
        task.status = TaskStatus.FAILED if has_failures else TaskStatus.DONE
        task.report = self.synthesizer.synthesize(task)
        _log.info(f"[NEXUS] Hedef tamamlandı. Durum: {task.status}")
        return task

    async def coordinate_architecture(self, proposal: Dict[str, Any]) -> bool:
        """
        Mimari bir öneriyi koordine eder: Denetim -> Scaffolding -> Görevlendirme.
        """
        from core.agi.security.audit_gate import AuditGate
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

    async def _execute_subtask_nexus(self, st: SubTask, parent_task: ProjectTask):
        """
        Bir alt görevi Nexus üzerinden yürütür. 
        Burada VelocityEngine devreye girer.
        """
        st.status = TaskStatus.RUNNING
        t_start = time.time()
        
        try:
            # --- Faz 17: Quantum Simülasyonu Entegrasyonu ---
            from core.agi.operational.velocity_engine import velocity_engine
            
            # Bağlam Genişletme (Contextual Expansion)
            enriched_context = await context_builder.build_context(
                agent_id=st.agent_id,
                task_text=st.prompt,
                project_id=parent_task.id
            )
            
            # Eylem simülasyonu ve yürütme (Look-Ahead Grounding)
            result = await velocity_engine.simulate_and_execute(
                agent_id=st.agent_id,
                prompt=st.prompt,
                context={"parent_goal": parent_task.title, "full_context": enriched_context},
                task_id=parent_task.id
            )
            
            if result.success:
                st.status = TaskStatus.DONE
                st.result = result.output_data if isinstance(result.output_data, str) else str(result.output_data)
                _log.info(f"[NEXUS] Başarılı yürütme: {st.agent_id}")
            else:
                st.status = TaskStatus.FAILED
                st.result = "; ".join(result.errors)
                _log.warning(f"[NEXUS] Yürütme başarısız: {st.agent_id}")
                
        except Exception as e:
            st.status = TaskStatus.FAILED
            st.result = str(e)
            _log.error(f"[NEXUS] Beklenmedik hata ({st.agent_id}): {e}")

        st.duration_s = time.time() - t_start

# --- Singleton ---
nexus_orchestrator = NexusOrchestrator()

def get_nexus_orchestrator() -> NexusOrchestrator:
    return nexus_orchestrator
