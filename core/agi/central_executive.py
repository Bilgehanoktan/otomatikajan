import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from agents.agent_registry import build_agents

# Bilişsel Birimlerin (Yeni Terminoloji) İçe Aktarımı
from core.agi.schemas import UnifiedInput, SourceType, EpisodeRecord, ContextPackage
from core.agi.cognitive.perception_unit import PerceptionUnit
from core.agi.cognitive.decision_matrix import DecisionMatrix
from core.agi.security.audit_gate import AuditGate
from memory.store import memory_store
from core.agi.cognitive.compactor import context_compactor
from db.session import session_scope

_log = get_logger("agi_central_executive")

class CentralExecutive:
    """
    Merkezi Yürütücü Birim (Central Executive).
    Geri Besleme Döngüsü (Mind Cycle) ve 4-Çekirdek mimarisini koordine eden en üst seviye yönetim birimi.
    Bilişsel (Algı/Karar), Operasyonel (Motor), Öğrenme (Hafıza) ve Güvenlik (Audit) katmanlarını yönetir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.agents = build_agents()
        
        # Uzman Ajanların (ECC 2.0 Skills) Keşfi
        from agents.agent_registry import discover_and_build_specialists
        self.specialists = discover_and_build_specialists()
        self.all_agents = {**self.agents, **self.specialists}
        
        # Bilişsel Birimlerin Başlatılması (Faz 17 Nexus-Quantum)
        self.perception = PerceptionUnit(self.model_orch)
        self.decision = DecisionMatrix(self.model_orch)
        
        from core.agi.operational.quantum_executor import QuantumExecutor
        self.motor = QuantumExecutor(self.model_orch)
        self.audit = AuditGate(self.model_orch)

    async def execute_thought_cycle(self, raw_input: Any, source: SourceType = SourceType.USER_MESSAGE) -> EpisodeRecord:
        """
        Bütünleşik Düşünce Döngüsü (Unified Thought Cycle). [Katman 17]
        1. Algıla -> 2. Kavra -> 3. Bağlam Kur -> 4. Karar Ver -> 5. Hareket Et -> 6. Denetle -> 7. Öğren
        """
        _log.info(f"Yürütme döngüsü başlatılıyor. Kaynak: {source.value}")
        
        # 1. Girdi ve Algı Katmanı (Perception Path)
        inp = UnifiedInput(source_type=source, raw_payload=raw_input)
        frame = await self.perception.perceive(inp)
        _log.info(f"Algılanan Hedef: {frame.task_type.value} - {frame.objective}")

        # --- Otonom Hedef Ayrıştırma (Decomposition) ---
        from core.agi.cognitive.decomposer import goal_decomposer
        sub_frames = await goal_decomposer.break_down(frame)
        
        # Eğer sadece tek frame varsa, standart akış devam eder.
        target_frames = sub_frames if len(sub_frames) > 1 else [frame]
        
        all_actions = []
        lessons_learned: List[str] = []
        cumulative_result = ""
        last_verification = None
        last_context = None
        last_decision_plan = None
        causal_graph = None
        summary = None
        
        for idx, current_frame in enumerate(target_frames):
            _log.info(f"Hiyerarşik Görev İşleniyor ({idx+1}/{len(target_frames)}): {current_frame.objective}")
            
            # --- Adaptif Strateji Belirleme ---
            from core.agi.adaptation.strategy_tuner import strategy_tuner
            from core.agi.monitoring.nervous_system import nervous_system
            sensory_metrics = {}
            async with session_scope() as db:
                sensory_metrics = await nervous_system.pulse(db)

            strategy = await strategy_tuner.determine_strategy(
                [], 
                current_frame,
                sensory_metrics=sensory_metrics
            )
            
            # 2. Epistemik Arama ve Bağlam Kurulumu
            from core.agi.world.repo_graph import repo_world_model
            repo_world_model.scan()
            summary = repo_world_model.get_summary()
            repo_context_pack = summary.get("context_pack", "")

            from core.agi.cognitive.perception_gate import perception_gate
            enriched_context = await perception_gate.probe(current_frame, f"{raw_input}\n\nÖnceki Adım Sonuçları: {cumulative_result}")
            
            reflection_context = enriched_context if enriched_context else ""
            current_attempt = 1
            max_attempts = strategy.max_attempts
            
            while current_attempt <= max_attempts:
                _log.info(f"YARIK (Task {idx+1}): Deneme {current_attempt}/{max_attempts}")
                
                # --- Global Bilgi Köprüsü ---
                from core.agi.learning.bridge import knowledge_bridge
                knowledge_bridge.set_current_project(str(inp.input_id))
                universal_hints = await knowledge_bridge.retrieve_universal_solution(current_frame.objective)
                if universal_hints:
                    universal_context = "\n".join([f"[GLOBAL_HINT]: {h['body']}" for h in universal_hints if h['confidence'] > 0.8])
                    reflection_context += f"\n{universal_context}"

                # --- Bağlam Sıkıştırma (Faz 13.2) ---
                working_summary = str(raw_input)
                if cumulative_result:
                    working_summary += f"\n\n[CUMULATIVE_HISTORY]: {cumulative_result}"
                
                if len(all_actions) > 5:
                    working_summary = await context_compactor.compact(all_actions, current_frame.objective)

                world_model_context = f"\n\n{repo_context_pack}" if repo_context_pack else ""
                reflection_block = f"\n\n[REFLECTION_CONTEXT]: {reflection_context}" if reflection_context else ""
                
                last_context = ContextPackage(
                    working_context=f"{working_summary}{reflection_block}{world_model_context}",
                    graph_links=[{
                        "hubs": summary["hubs"],
                        "critical": summary["critical_files"],
                    }],
                    relevant_skills=list(self.specialists.keys()),
                    policy_hints=["Memory is append-only.", f"Parent Goal: {frame.objective}"],
                )
                
                # 3. Karar Verme Katmanı
                last_decision_plan = await self.decision.decide(current_frame, last_context)
                
                # --- Karar Konsensüsü (Basitleştirilmiş Faz 17) ---
                plan = last_decision_plan
                
                # --- Simülasyon Kapısı (Foresight v16.1 Entegrasyonu) ---
                from core.agi.cognitive.foresight_oracle import foresight_oracle
                sim_risks = await foresight_oracle.simulate_plan(plan)
                if sim_risks:
                    _log.info(f"Foresight: Plan simüle edildi, {len(sim_risks)} risk noktası saptandı.")

                # 4. Hareket Katmanı (Quantum Executor - Simüle Edilmiş Yürütme)
                action_res = await self.motor.simulate_and_execute(
                    agent_id=plan.steps[0].agent_id if plan.steps else "unknown",
                    prompt=plan.goal,
                    context=last_context.__dict__ if hasattr(last_context, "__dict__") else {},
                    task_id=str(inp.input_id)
                )
                
                # ActionRecord formatına dönüştür (Legacy uyum)
                from core.agi.schemas import ActionRecord
                record = ActionRecord(
                    plan_id=plan.plan_id,
                    step_id="step_1",
                    tool_used=plan.steps[0].agent_id if plan.steps else "unknown",
                    input_data=plan.goal,
                    output_data=action_res.output_data,
                    success=action_res.success,
                    timestamp=datetime.now(timezone.utc)
                )
                actions = [record]
                all_actions.extend(actions)
                step_result = actions[-1].output_data if actions else "No output"
                cumulative_result += f"\nStep {idx+1} Output: {step_result}"

                # 5. Denetim (Audit Gate)
                verification = await self.audit.verify(current_frame, actions, step_result)
                last_verification = verification
                _log.info(f"Denetim Sonucu: {verification.result_status} | Reality Score: {verification.integration_reality_score}")
                
                if verification.result_status:
                    _log.info(f"Alt Görev {idx+1} BAŞARILI.")
                    if verification.evidence_summary:
                        lessons_learned.append(f"Task {idx+1} Verification: {verification.evidence_summary}")
                    break
                else:
                    current_attempt += 1
                    lessons_learned.append(f"Sub-task {idx+1} failed: {verification.evidence_summary}")
                    _log.warning(f"Alt Görev {idx+1} başarısız deneme. Refleksiyon yapılıyor...")
            
            if not last_verification or not last_verification.result_status:
                _log.error(f"Hiyerarşik yürütme ALT GÖREV {idx+1} aşamasında DURDU.")
                
                # Nedensellik Analizi (Hata Durumunda)
                from core.agi.cognitive.causal_engine import causal_engine
                temp_ep = EpisodeRecord(problem_frame=current_frame, actions=all_actions, verification=last_verification)
                causal_graph = await causal_engine.analyze_episode(temp_ep)
                break

        # 6. Hafıza ve Öğrenme Katmanı (Memory Core)
        episode = EpisodeRecord(
            input_obj=inp,
            problem_frame=frame,
            context_used=last_context,
            plan=last_decision_plan,
            actions=all_actions,
            verification=last_verification,
            final_output=cumulative_result,
            causal_graph=causal_graph,
            lessons_learned=lessons_learned,
            world_model_updates=[{
                "root_dir": summary.get("root_dir") if summary else None,
                "total_files": summary.get("total_files") if summary else 0,
            }],
            timestamp=datetime.now(timezone.utc)
        )
        episode.importance = 0.8 if last_verification and last_verification.result_status else 0.55
        
        async with session_scope() as db:
            if await memory_store.memory_write_gate(db, episode, "episode_record"):
                await memory_store.save_episode(db, {
                    "title": frame.objective,
                    "status": "success" if last_verification and last_verification.result_status else "failed",
                    "project_id": str(inp.input_id),
                    "final_output": str(cumulative_result)[:2000],
                    "verification_summary": getattr(last_verification, "evidence_summary", ""),
                    "lessons_learned": episode.lessons_learned,
                })
                _log.info("Bölüm (Episode) hafızaya konsolide edildi.")

                # Otonom Beceri Ayrıştırma (Skill Distillation)
                if last_verification and last_verification.result_status and last_verification.integration_reality_score >= 0.7:
                    from core.agi.learning.distiller import skill_distiller
                    await skill_distiller.distill(episode, db)
                
                # Otonom Adaptasyon ve Politika Evrimi
                try:
                    from core.agi.adaptation.policy_engine import policy_engine
                    asyncio.create_task(policy_engine.evolve(db))
                except Exception as pe:
                    _log.warning(f"Policy evolution başlatılamadı: {pe}")
        
        return episode

# --- Singleton ---
central_executive = CentralExecutive()
