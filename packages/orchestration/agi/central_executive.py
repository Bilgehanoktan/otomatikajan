import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc # Faz 82-85: Strategic Query
from packages.observability.logging import get_logger
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.orchestration.agi.operational.local_failsafe_engine import local_failsafe
from packages.orchestration.agi.agents.agent_registry import build_agents

# Bilişsel Birimlerin (Cortex Mimarisi) İçe Aktarımı
from packages.orchestration.agi.schemas import (
    UnifiedInput, SourceType, EpisodeRecord, ContextPackage, RiskLevel, TaskType
)
from packages.orchestration.agi.cognitive.perception_unit import PerceptionUnit
from packages.orchestration.agi.cognitive.strategic_decision_center import StrategicDecisionCenter
from packages.orchestration.agi.security.audit_gate import AuditGate
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from packages.orchestration.agi.cognitive.compactor import context_compactor
from packages.orchestration.agi.cognitive.motivation_engine import motivation_engine # Phase 28
from packages.orchestration.agi.cognitive.thread_governor import thread_governor # Phase 63
from packages.persistence.session import session_scope

# WorldModel Katman 9: Observability & Graph Context
from packages.orchestration.agi.world import service_graph, task_state_graph, causal_error_graph
from packages.persistence.repositories.repository import EventLogRepository # Faz 85: Cognitive Logging

_log = get_logger("agi_central_executive")

class CentralExecutive:
    """
    Merkezi Yürütücü Birim (Central Executive). [Faz 51: Sovereign Depth]
    DAG tabanlı yürütme ve rekürsif dekompozisyon desteği ile evrimleşmiş zihin döngüsü.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.agents = build_agents()
        
        # Uzman Ajanların (ECC 2.0 Skills) Keşfi
        from packages.orchestration.agi.agents.agent_registry import discover_and_build_specialists
        self.specialists = discover_and_build_specialists()
        self.all_agents = {**self.agents, **self.specialists}
        
        self.perception = PerceptionUnit(self.model_orch)
        self.decision = StrategicDecisionCenter(self.model_orch)
        
        from packages.orchestration.agi.operational.motor_synapse import MotorSynapse
        from packages.orchestration.agi.operational.velocity_engine import velocity_engine
        self.motor_synapse = MotorSynapse(self.all_agents)
        self.velocity_engine = velocity_engine
        self.audit = AuditGate(self.model_orch)

    async def execute_thought_cycle(self, raw_input: Any, source: SourceType = SourceType.USER_MESSAGE, input_id: Optional[str] = None) -> EpisodeRecord:
        """
        Bütünleşik Düşünce Döngüsü (Unified Thought Cycle).
        Faz 51: DAG Dalga Yürütme ve Rekürsif Derinlik.
        """
        _log.info(f"Yürütme döngüsü başlatılıyor. Kaynak: {source.value}")
        
        async with session_scope() as db:
            from packages.orchestration.agi.cognitive.theory_of_mind import theory_of_mind
            await theory_of_mind.load_state(db, str(input_id) if input_id else "global")
            theory_of_mind.analyze_interaction(str(raw_input))
            
            # Phase 63: Bilişsel Devamlılık Ünitesini Yükle (Thread context)
            active_thread = await thread_governor.get_active_thread(db, str(input_id) if input_id else "global")
            _log.info(f"[THREAD-LOADED] Mevcut Monolog: {active_thread[:80]}...")
            
            # Phase 82: North Star Goal Alignment (Executive Context)
            from apps.worker.tasks.celery_app import celery_app  # type: ignore
            from apps.worker.tasks.project_tasks import run_project_task  # type: ignore
            from packages.persistence.models import SovereignGoal
            stmt = select(SovereignGoal).where(SovereignGoal.status == "active").order_by(desc(SovereignGoal.priority))
            res = await db.execute(stmt)
            active_goal = res.scalars().first()
            if active_goal:
                _log.info(f"[NORTH-STAR-ACTIVE] Vizyon: {active_goal.title}")
        
        # 1. Algı Katmanı
        inp = UnifiedInput(source_type=source, raw_payload=raw_input, input_id=str(input_id) if input_id else str(uuid.uuid4()))
        frame = await self.perception.perceive(inp)
        
        # 2. Motivasyon Kalibrasyonu
        async with session_scope() as db:
            recent_episodes = await synaptic_cortex.search(db, query="", category="episode_record", top_k=5)
        affective_state = await motivation_engine.recalibrate_state(recent_episodes, frame)

        # 3. [FAZ 51] Stratejik Dekompozisyon ve DAG
        from packages.orchestration.agi.cognitive.sovereign_planner import sovereign_planner
        sub_frames = await sovereign_planner.decompose(frame.objective, frame.objective, list(self.all_agents.values()))
        execution_waves = sovereign_planner.get_execution_waves(sub_frames)
        
        cumulative_result = ""
        all_actions = []
        lessons_learned = []
        running_synapse_lessons = [] # Phase 66: Causal Anchoring
        last_verification = None
        last_context = None
        last_decision_plan = None
        causal_graph = None

        # 4. Dalga Yürütme (Wave Execution)
        for wave_idx, wave_tasks in enumerate(execution_waves):
            _log.info(f"[WAVE {wave_idx}] {len(wave_tasks)} görev yürütülüyor.")
            
            for current_frame in wave_tasks:
                # Rekürsif Kontrol
                if getattr(current_frame, "is_complex", False):
                    _log.info(f"[RECURSION] Karmaşık görev: {current_frame.objective}")
                    sub_ep = await self.execute_thought_cycle(
                        current_frame.prompt, 
                        source=SourceType.SYSTEM_COMMAND, 
                        input_id=f"{inp.input_id}_{current_frame.id}"
                    )
                    cumulative_result += f"\n[SUB-PLAN RESULT]: {sub_ep.final_output}"
                    continue

                # Normal Görev Yürütme
                task_res = await self._execute_task_frame(
                    current_frame, inp, cumulative_result, affective_state, 
                    running_synapse_lessons, thought_thread=active_thread,
                    north_star_goal=active_goal # Phase 82
                )
                
                if task_res["success"]:
                    # Phase 63: Monoloğu Güncelle
                    async with session_scope() as db:
                        await thread_governor.update_thread(
                            db, str(inp.input_id), 
                            f"Executed Task: {current_frame.objective}", 
                            f"Result: {str(task_res['output'])[:500]}..."
                        )
                        # Yeni monoloğu bir sonraki adım için tazele
                        active_thread = await thread_governor.get_active_thread(db, str(inp.input_id))
                
                cumulative_result += f"\n[TASK OUTPUT]: {task_res['output']}"
                all_actions.extend(task_res["actions"])
                if task_res["verification"]:
                    last_verification = task_res["verification"]
                    if task_res["verification"].evidence_summary:
                        lessons_learned.append(task_res["verification"].evidence_summary)
                
                if task_res["causal_graph"]:
                    causal_graph = task_res["causal_graph"]
                    # Phase 66: Causal Insight ekle
                    running_synapse_lessons.append({
                        "source_task": current_frame.id,
                        "lesson": f"Failure analyzed: {causal_graph.links[0].relationship_type if causal_graph.links else 'Unknown cause'}",
                        "type": "causal_anchor"
                    })

                if task_res["success"] and task_res["verification"]:
                    # Başarılı adımdan ders çıkar
                    running_synapse_lessons.append({
                        "source_task": current_frame.id,
                        "lesson": task_res["verification"].evidence_summary,
                        "type": "success_anchor"
                    })

                if not task_res["success"]:
                    _log.warning(f"Görev {current_frame.id} başarısız. Stratejik duruş alınıyor.")
                    # Burada hata kurtarma veya durma mantığı çalışabilir
                    break

        # 5. Hafıza ve Metacognitive Analiz
        from packages.orchestration.agi.cognitive.metacognition import metacognition
        trace_analysis = await metacognition.analyze_cognitive_trace(all_actions)
        
        episode = EpisodeRecord(
            input_obj=inp, problem_frame=frame, context_used=None, 
            plan=None, actions=all_actions, verification=last_verification,
            final_output=cumulative_result, causal_graph=causal_graph,
            lessons_learned=lessons_learned, affective_state=affective_state,
            metacognitive_score=trace_analysis.get("success_rate", 1.0),
            timestamp=datetime.now(timezone.utc)
        )
        
        async with session_scope() as db:
            from packages.orchestration.agi.cognitive.theory_of_mind import theory_of_mind
            await theory_of_mind.persist_state(db, str(input_id) if input_id else "global")

            if await synaptic_cortex.memory_write_gate(db, episode, "episode_record"):
                await synaptic_cortex.save_episode(db, {
                    "title": frame.objective,
                    "status": "success" if last_verification and last_verification.result_status else "failed",
                    "project_id": str(inp.input_id),
                    "final_output": str(cumulative_result)[:2000],
                    "metacognitive_score": episode.metacognitive_score
                })
        
        return episode

    async def _execute_task_frame(self, current_frame, inp, cumulative_history, affective_state, synapse_lessons: List[Dict[str, Any]] = None, thought_thread: str = "", north_star_goal: Any = None) -> Dict[str, Any]:
        """Tek bir görev birimini (frame) yürütür."""
        from packages.orchestration.agi.adaptation.strategy_tuner import strategy_tuner
        from packages.orchestration.agi.monitoring.nervous_system import nervous_system
        
        async with session_scope() as db:
            sensory_metrics = await nervous_system.pulse(db)
        
        from packages.orchestration.agi.world.repo_graph import repo_world_model
        repo_world_model.scan()
        summary = repo_world_model.get_summary()

        current_attempt = 1
        max_attempts = strategy.max_attempts
        success = False
        task_actions = []
        final_output = ""
        last_verification = None
        while current_attempt <= max_attempts:
            # Phase 84: Dynamic Runtime Re-Tuning
            strategy = await strategy_tuner.determine_strategy(
                [], current_frame, sensory_metrics=sensory_metrics, failed_attempts=current_attempt - 1
            )
            
            # Phase 85: Cognitive Event Logging
            if current_attempt > 1:
                async with session_scope() as db:
                    await EventLogRepository.write(
                        db, event_type="cognitive_escalation", severity="warning",
                        message=f"Görev denemesi {current_attempt}. Strateji tırmandırıldı: attempts={strategy.max_attempts}, sim={strategy.simulation_required}",
                        agent_id="central_executive", phase="runtime_adaptation"
                    )
                    
            max_attempts = strategy.max_attempts # Update limit if strategy escalates
            
            ctx = ContextPackage(
                working_context=f"History: {cumulative_history}",
                graph_links=[{"hubs": summary["hubs"]}],
                relevant_skills=list(self.specialists.keys()),
                affective_context=affective_state,
                synapse_lessons=synapse_lessons or [], # Phase 66
                thought_thread=thought_thread, # Phase 63
                north_star_vision=f"Goal: {north_star_goal.title}\nVision: {north_star_goal.vision_statement}" if north_star_goal else "Standard Autonomy", # Phase 82
                integrity_status=await self._get_integrity_status()
            )

            try:
                plan = await self.decision.decide(current_frame, ctx)
                agent_id = plan.steps[0].agent_id if plan.steps else "architect"
                
                res = await self.velocity_engine.simulate_and_execute(
                    agent_id=agent_id, prompt=plan.goal, context=ctx.__dict__, task_id=str(inp.input_id)
                )
                
                final_output = res.output_data
                from packages.orchestration.agi.schemas import ActionRecord
                rec = ActionRecord(
                    plan_id=plan.plan_id, step_id="s1", tool_used=agent_id,
                    input_data=current_frame.objective, output_data=final_output,
                    success=res.success, timestamp=datetime.now(timezone.utc)
                )
                task_actions.append(rec)
                
                last_verification = await self.audit.verify(current_frame, task_actions, final_output)
                if last_verification.result_status:
                    success = True
                    break
                current_attempt += 1
            except Exception as e:
                _log.error(f"Execution error: {e}")
                current_attempt += 1

        causal_graph = None
        if not success:
            from packages.orchestration.agi.cognitive.causal_engine import causal_engine
            temp_ep = EpisodeRecord(problem_frame=current_frame, actions=task_actions, verification=last_verification)
            causal_graph = await causal_engine.analyze_episode(temp_ep, depth=2)

        return {
            "success": success, "output": final_output, "actions": task_actions,
            "verification": last_verification, "causal_graph": causal_graph
        }

    async def _get_integrity_status(self) -> Dict[str, Any]:
        orch_health = self.model_orch.get_health_score() if hasattr(self, "model_orch") else 1.0
        return {"mode": "nominal", "health": orch_health}

# Singleton
central_executive = CentralExecutive()
