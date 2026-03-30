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
        
        # Discover Specialists from ECC 2.0 Skills (Phase 12.4)
        from agents.agent_registry import discover_and_build_specialists
        self.specialists = discover_and_build_specialists()
        self.all_agents = {**self.agents, **self.specialists}
        
        # Initialize Cores
        self.interpreter = IntentInterpreter(self.model_orch)
        self.planner = CognitivePlanner(self.model_orch)
        self.executor = OperationalExecutor(self.all_agents)
        self.audit = AuditGate(self.model_orch)

    async def run(self, raw_input: Any, source: SourceType = SourceType.USER_MESSAGE) -> EpisodeRecord:
        """
        Uçtan uca AGI veri akışı.
        1. Normalize -> 2. Interpret -> 3. Context -> 4. Plan -> 5. Execute -> 6. Verify -> 7. Reflect -> 8. Learn
        """
        _log.info(f"AGI Akışı başlatılıyor. Kaynak: {source.value}")
        
        # 1. Input Layer (Katman 1)
        inp = UnifiedInput(source_type=source, raw_payload=raw_input)
        
        # 1. Perception & Interpretation Layer (Katman 2)
        frame = await self.interpreter.interpret(inp)
        _log.info(f"Problem Tanımlandı: {frame.task_type.value} - {frame.objective}")

        # --- Otonom Hedef Ayrıştırma (Phase 12.9) ---
        from core.agi.cognitive.decomposer import goal_decomposer
        sub_frames = await goal_decomposer.break_down(frame)
        if len(sub_frames) > 1:
            _log.info(f"Karmaşık Hedef {len(sub_frames)} Alt Göreve Bölündü.")
        
        # TODO: Rekürsif yürütme için sub_frames döngüsü burada kurulabilir.
        # Şimdilik en üst seviyedeki frame ile devam et.

        # --- Otonom Strateji Belirleme (Phase 12.7 / 18.0) ---
        from core.agi.adaptation.strategy_tuner import strategy_tuner
        from core.agi.monitoring.nervous_system import nervous_system
        from db.session import session_scope
        sensory_metrics = {}
        async with session_scope() as db:
            sensory_metrics = await nervous_system.pulse(db)

        strategy = await strategy_tuner.determine_strategy(
            [], 
            frame,
            sensory_metrics=sensory_metrics
        )
        
        # 3. Cognitive Planning Layer (Katman 3) - Context Building (ENHANCED)
        from core.agi.world.repo_graph import repo_world_model
        _log.info("Dünya Modeli (Repo Graph) taranıyor...")
        repo_world_model.scan()
        summary = repo_world_model.get_summary()

        # --- Aktif Algı / Epistemic Agency (Phase 12.6) ---
        from core.agi.cognitive.perception_gate import perception_gate
        enriched_context = await perception_gate.probe(frame, str(raw_input))
        if enriched_context:
            _log.info("Bağlam Zenginleştirildi (Perception Gate).")

        # Otonom Refleksiyon ve Öz-Düzeltme Döngüsü (Phase 12.3)
        max_attempts = strategy.max_attempts
        current_attempt = 1
        reflection_context = enriched_context if enriched_context else ""
        causal_graph = None
        all_actions = []
        last_verification = None
        final_result = None
        
        while current_attempt <= max_attempts:
            _log.info(f"DÖNGÜ: Deneme {current_attempt}/{max_attempts}")
            
            # --- Global Bilgi Köprüsü (Phase 12.5) ---
            from core.agi.learning.bridge import knowledge_bridge
            knowledge_bridge.set_current_project(str(inp.input_id))
            universal_hints = await knowledge_bridge.retrieve_universal_solution(frame.objective)
            if universal_hints:
                universal_context = "\n".join([f"[GLOBAL_HINT]: {h['body']}" for h in universal_hints if h['confidence'] > 0.8])
                reflection_context += f"\n{universal_context}"

            # --- Politika Enjeksiyonu (Phase 12.10) ---
            from core.agi.adaptation.policy_enforcer import policy_enforcer
            from db.session import session_scope
            async with session_scope() as db:
                active_policies = await policy_enforcer.get_active_policies(db)
                if active_policies:
                    reflection_context += "\n" + "\n".join(active_policies)

            context = ContextPackage(
                working_context=f"{raw_input}\n\n[REFLECTION_CONTEXT]: {reflection_context}" if reflection_context else str(raw_input),
                graph_links=[{"hubs": summary["hubs"], "critical": summary["critical_files"]}],
                relevant_skills=list(self.specialists.keys()) # Plannera mevcut becerileri bildir
            )
            
            # 4. Cognitive Planning Layer (Katman 3) - Planning (ENHANCED WITH CONSENSUS)
            plan = await self.planner.create_plan(frame, context)
            
            # --- Plan Konsensüsü (Phase 12.8 / 19.0: Cognitive Debate) ---
            if strategy.consensus_required:
                from core.agi.cognitive.consensus_manager import consensus_manager
                from core.agi.cognitive.debate_manager import debate_manager
                
                # Alternatif bir plan üret
                alt_plan = await self.planner.create_plan(frame, context)
                
                # Bilişsel Tartışma (Debate)
                debated_proposals = await debate_manager.argue([plan, alt_plan], str(context))
                
                # Diyalektik Konsensüs
                plan = await consensus_manager.resolve(debated_proposals, str(context))
                _log.info("Plan Tartışıldı ve Konsensüs ile Onaylandı.")

            _log.info(f"Plan Oluşturuldu: {len(plan.steps)} adım.")

            # 4.5 Simulation Gate (Katman 3 / Gate 4)
            if strategy.simulation_required:
                from core.agi.cognitive.simulator import simulation_engine
                simulation_report = await simulation_engine.simulate(frame, plan)
                if simulation_report.get("status") == "completed":
                    _log.info(f"Simülasyon Tamamlandı. Tahmin Edilen Başarı: {simulation_report.get('predicted_success_rate')}")

            # 5. Operational Execution Layer (Katman 5)
            actions = await self.executor.execute_plan(plan)
            all_actions.extend(actions)
            final_result = actions[-1].output_data if actions else "No actions performed"

            # 6. Verification and Critique Layer (Katman 6)
            verification = await self.audit.verify(frame, actions, final_result)
            last_verification = verification
            _log.info(f"Doğrulama Sonucu: {verification.result_status} | Reality Score: {verification.integration_reality_score}")

            if verification.result_status:
                _log.info("Görev başarıyla tamamlandı, döngü sonlanıyor.")
                break
            else:
                # --- Nedensel Teşhis (Phase 12.5) ---
                current_attempt += 1
                from core.agi.cognitive.causal_engine import causal_engine
                # Geçici bir episode oluşturup analiz et
                temp_ep = EpisodeRecord(problem_frame=frame, actions=actions, verification=verification)
                causal_graph = await causal_engine.analyze_episode(temp_ep)
                
                diagnosis = causal_graph.nodes_metadata.get("failure_reason_summary", "Unknown failure")
                root_cause = causal_graph.nodes_metadata.get("root_cause_step", "Unknown")
                
                reflection_context = f"BAŞARISIZLIK TEŞHİSİ: {diagnosis}. Kök Neden: {root_cause}. Lütfen bu adımı ve bağımlılıklarını düzelterek yeni bir plan yap."
                _log.warning(f"Nedensel Refleksiyon: {reflection_context}")

        # 7. Memory and Learning Layer (Katman 7)
        episode = EpisodeRecord(
            input_obj=inp,
            problem_frame=frame,
            context_used=None, # Re-built inside loop
            plan=None,        # Final plan used
            actions=all_actions,
            verification=last_verification,
            final_output=final_result,
            causal_graph=causal_graph, # Phase 12.5
            timestamp=datetime.now(timezone.utc)
        )
        
        # Memory Write Gate & Learning Core
        from db.session import session_scope
        async with session_scope() as db:
            if await memory_store.memory_write_gate(db, episode, "episode_record"):
                # Episode kaydet
                await memory_store.save_episode(db, {
                    "title": frame.objective,
                    "status": "success" if last_verification and last_verification.result_status else "failed",
                    "project_id": str(inp.input_id),
                    "final_output": str(final_result or "")[:2000]
                })
                _log.info("Episode hafızaya kaydedildi.")

                # Otonom Öğrenme (Skill Distillation)
                if last_verification and last_verification.result_status and last_verification.integration_reality_score >= 0.7:
                    from .learning.distiller import skill_distiller
                    await skill_distiller.distill(episode, db)
                
                # Otonom İyileştirme (Phase 12.4 - Tool Optimization)
                from .learning.tool_optimizer import tool_optimizer
                await tool_optimizer.optimize_dynamic_tools(episode, db)
                
                # Otonom Adaptasyon (Phase 12.3 - Policy Engine)
                from .adaptation.policy_engine import policy_engine
                await policy_engine.evolve(db)
        
        return episode

# --- Singleton ---
agi_orchestrator = AGIOrchestrator()
