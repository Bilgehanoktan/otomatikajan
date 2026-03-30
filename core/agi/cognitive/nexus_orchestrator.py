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
        
        task = ProjectTask(id=task_id, title=title)
        # Niyet Odaklı Dekompozisyon (Intent-Based Decomposition)
        task.subtasks = self.planner.plan(title, description)
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

    async def _execute_subtask_nexus(self, st: SubTask, parent_task: ProjectTask):
        """
        Bir alt görevi Nexus üzerinden yürütür. 
        Burada QuantumExecutor devreye girer.
        """
        st.status = TaskStatus.RUNNING
        t_start = time.time()
        
        try:
            # --- Faz 17: Quantum Simülasyonu Entegrasyonu ---
            from core.agi.operational.quantum_executor import quantum_executor
            
            # Bağlam Genişletme (Contextual Expansion)
            enriched_context = await context_builder.build_context(
                agent_id=st.agent_id,
                task_text=st.prompt,
                project_id=parent_task.id
            )
            
            # Eylem simülasyonu ve yürütme (Look-Ahead Grounding)
            result = await quantum_executor.simulate_and_execute(
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
