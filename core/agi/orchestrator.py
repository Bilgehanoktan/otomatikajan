import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from agents.agent_registry import build_agents

# Import 4-core components
from core.agi.schemas import UnifiedInput, SourceType, EpisodeRecord, ContextPackage
from core.agi.cognitive.interpreter import IntentInterpreter
from core.agi.cognitive.planner import CognitivePlanner
from core.agi.operational.executor import OperationalExecutor
from core.agi.security.audit_gate import AuditGate
from memory.store import memory_store

_log = get_logger("agi_orchestrator")

class AGIOrchestrator:
    """
    AGI-Oriented Orchestrator Coordinating the 4-Core Architecture.
    Bilişsel, Operasyonel, Öğrenme ve Güvenlik/Denetim Çekirdeklerini yönetir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.agents = build_agents()
        
        # Initialize Cores
        self.interpreter = IntentInterpreter(self.model_orch)
        self.planner = CognitivePlanner(self.model_orch)
        self.executor = OperationalExecutor(self.agents)
        self.audit = AuditGate(self.model_orch)

    async def run(self, raw_input: Any, source: SourceType = SourceType.USER_MESSAGE) -> EpisodeRecord:
        """
        Uçtan uca AGI veri akışı.
        1. Normalize -> 2. Interpret -> 3. Context -> 4. Plan -> 5. Execute -> 6. Verify -> 7. Learn
        """
        _log.info(f"AGI Akışı başlatılıyor. Kaynak: {source.value}")
        
        # 1. Input Layer (Katman 1)
        inp = UnifiedInput(source_type=source, raw_payload=raw_input)
        
        # 2. Perception & Interpretation Layer (Katman 2)
        frame = await self.interpreter.interpret(inp)
        _log.info(f"Problem Tanımlandı: {frame.task_type.value} - {frame.objective}")

        # 3. Cognitive Planning Layer (Katman 3) - Context Building
        # Not: Basit bağlam, gelişmiş Graph bağlamı ileride eklenebilir.
        context = ContextPackage(working_context=str(raw_input))
        
        # 4. Cognitive Planning Layer (Katman 3) - Planning
        plan = await self.planner.create_plan(frame, context)
        _log.info(f"Plan Oluşturuldu: {len(plan.steps)} adım.")

        # 5. Operational Execution Layer (Katman 5)
        actions = await self.executor.execute_plan(plan)
        final_result = actions[-1].output_data if actions else "No actions performed"

        # 6. Verification and Critique Layer (Katman 6)
        verification = await self.audit.verify(frame, actions, final_result)
        _log.info(f"Doğrulama Tamamlandı. Durum: {verification.result_status}")

        # 7. Memory and Learning Layer (Katman 7)
        episode = EpisodeRecord(
            input_obj=inp,
            problem_frame=frame,
            context_used=context,
            plan=plan,
            actions=actions,
            verification=verification,
            final_output=final_result,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Memory Write Gate
        # DB oturumu gerektirdiği için memory_store'u burada çağırmıyoruz, 
        # ama yetki kontrolü yapıyoruz.
        from db.session import session_scope
        async with session_scope() as db:
            if await memory_store.memory_write_gate(db, episode, "episode_record"):
                await memory_store.save_episode(db, {
                    "title": frame.objective,
                    "status": "success" if verification.result_status else "failed",
                    "project_id": str(inp.input_id),
                    "final_output": str(final_result)[:2000]
                })
                _log.info("Episode hafızaya kaydedildi.")
        
        return episode

# --- Singleton ---
agi_orchestrator = AGIOrchestrator()
