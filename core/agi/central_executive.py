import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from core.agi.operational.local_failsafe_engine import local_failsafe
from agents.agent_registry import build_agents

# Bilişsel Birimlerin (Cortex Mimarisi) İçe Aktarımı
from core.agi.schemas import (
    UnifiedInput, SourceType, EpisodeRecord, ContextPackage, RiskLevel, TaskType
)
from core.agi.cognitive.perception_unit import PerceptionUnit
from core.agi.cognitive.strategic_decision_center import StrategicDecisionCenter
from core.agi.security.audit_gate import AuditGate
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from core.agi.cognitive.compactor import context_compactor
from core.agi.cognitive.motivation_engine import motivation_engine # Phase 28
from db.session import session_scope

# WorldModel Katman 9: Observability & Graph Context
from core.agi.world import service_graph, task_state_graph, causal_error_graph

_log = get_logger("agi_central_executive")

class CentralExecutive:
    """
    Merkezi Yürütücü Birim (Central Executive).
    Geri Besleme Döngüsü (Mind Cycle) ve 4-Çekirdek mimarisini koordine eden en üst seviye yönetim birimi.
    Bilişsel (Algı/Karar), Operasyonel (Eylem), Öğrenme (Hafıza) ve Güvenlik (Audit) katmanlarını yönetir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.agents = build_agents()
        
        # Uzman Ajanların (ECC 2.0 Skills) Keşfi
        from agents.agent_registry import discover_and_build_specialists
        self.specialists = discover_and_build_specialists()
        self.all_agents = {**self.agents, **self.specialists}
        
        # Bilişsel Birimlerin Başlatılması (Faz 16 Bio-Evolution)
        self.perception = PerceptionUnit(self.model_orch)
        self.decision = StrategicDecisionCenter(self.model_orch)
        
        from core.agi.operational.motor_synapse import MotorSynapse
        from core.agi.operational.velocity_engine import velocity_engine
        self.motor_synapse = MotorSynapse(self.all_agents)
        self.velocity_engine = velocity_engine
        self.audit = AuditGate(self.model_orch)

    async def execute_thought_cycle(self, raw_input: Any, source: SourceType = SourceType.USER_MESSAGE, input_id: Optional[str] = None) -> EpisodeRecord:
        """
        Bütünleşik Düşünce Döngüsü (Unified Thought Cycle). [Katman 17]
        1. Algıla -> 2. Kavra -> 3. Bağlam Kur -> 4. Karar Ver -> 5. Hareket Et -> 6. Denetle -> 7. Öğren
        """
        _log.info(f"Yürütme döngüsü başlatılıyor. Kaynak: {source.value}")
        
        async with session_scope() as db:
            # 0. Theory of Mind: Kullanıcı Modelini Yükle (Phase 22)
            from core.agi.cognitive.theory_of_mind import theory_of_mind
            await theory_of_mind.load_state(db, str(input_id) if input_id else "global")
            theory_of_mind.analyze_interaction(str(raw_input))
        
        # 1. Girdi ve Alg Katman (Perception Path)
        inp = UnifiedInput(source_type=source, raw_payload=raw_input, input_id=str(input_id) if input_id else str(uuid.uuid4()))
        frame = await self.perception.perceive(inp)
        _log.info(f"Algılanan Hedef: {frame.task_type.value} - {frame.objective}")
        
        # --- Affective Core: Motivasyon Kalibrasyonu (Phase 28) ---
        recent_episodes = [] 
        async with session_scope() as db:
            # Son 5 bölümü başarı/başarısızlık oranı için getir
            recent_episodes = await synaptic_cortex.search(db, query="", category="episode_record", top_k=5)
            
        affective_state = await motivation_engine.recalibrate_state(recent_episodes, frame)

        # --- Otonom Hedef Ayrıştırma (Decomposition) ---
        from core.agi.cognitive.sovereign_planner import sovereign_planner as goal_decomposer
        sub_frames = await goal_decomposer.decompose(frame.objective, frame.description, list(self.all_agents.values()))
        
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

            # --- Swarm Mode Detection (Faz 18) ---
            independent_frames = [f for f in target_frames[idx:] if not f.dependencies or all(d in [tf.id for tf in target_frames[:idx]] for d in f.dependencies)]
            
            if len(independent_frames) > 1 and idx == 0:
                _log.info(f"[SWARM] {len(independent_frames)} bağımsız görev saptandı. Paralel yürütme (Swarm Mode) başlatılıyor.")
                swarm_actions = []
                for sf in independent_frames:
                    # Basit karar verme (her biri için hızlıca karar al)
                    swarm_actions.append({"agent_id": "architect", "prompt": sf.objective})
                
                swarm_results = await self.velocity_engine.execute_swarm(swarm_actions, {}, str(inp.input_id))
                for s_idx, s_res in enumerate(swarm_results):
                    cumulative_result += f"\nSwarm Task {s_idx+1} Output: {s_res.output_data}"
                
                # Swarm sonrası indexi güncelle veya döngüden çık (basitleştirilmiş)
                # Gerçekte daha karmaşık bir bağımlılık ağacı yönetimi gerekir.
            
            strategy = await strategy_tuner.determine_strategy(
                [], 
                current_frame,
                sensory_metrics=sensory_metrics
            )
            
            # 2. Epistemik Arama ve Bağlam Kurulumu
            from core.agi.world.repo_graph import repo_world_model
            repo_world_model.scan()
            
            # Katman 9: Servis Sağlığı ve Görev Geçmişi
            service_health = service_graph.get_health_report()
            task_history = task_state_graph.get_summary()
            
            summary = repo_world_model.get_summary()
            repo_context_pack = summary.get("context_pack", "")
            
            # Entegre Dünya Modeli Bağlamı
            world_context = f"{repo_context_pack}\n\n[SERVICE_HEALTH]: {service_health}\n[TASK_HISTORY]: {task_history}"

            from core.agi.cognitive.perception_gate import perception_gate
            enriched_context = await perception_gate.probe(current_frame, f"{raw_input}\n\n{world_context}\n\nÖnceki Adım Sonuçları: {cumulative_result}")
            
            reflection_context = enriched_context if enriched_context else ""
            current_attempt = 1
            # Motivasyon motoru çarpanı ile dinamik max_attempts
            max_attempts = strategy.max_attempts * motivation_engine.get_persistence_multiplier()
            _log.info(f"[MOTIVATION] Persistence Mode: {affective_state.persistence_policy} | Max Attempts: {max_attempts}")
            
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
                
                # Faz 22: SynapticCortex (Bilinçaltı) Derslerini Getir
                synapse_lessons = []
                async with session_scope() as db:
                    synapse_lessons = await synaptic_cortex.search(db, query="", category="policy_proposal", top_k=5)
                    synapse_lessons += await synaptic_cortex.search(db, query="", category="reflection_log", top_k=5)

                # State Awareness: Bütünlük Durumu Enjeksiyonu (Faz 12.2)
                integrity = await self._get_integrity_status()

                # --- Affective Context Extension (Faz 12.3) ---
                # affective_state zaten yukarıda (satır 72) recalibrate edildi
                
                last_context = ContextPackage(
                    working_context=f"{working_summary}{reflection_block}{world_model_context}",
                    graph_links=[{
                        "hubs": summary["hubs"],
                        "critical": summary["critical_files"],
                    }],
                    relevant_skills=list(self.specialists.keys()),
                    policy_hints=["Memory is append-only.", f"Parent Goal: {frame.objective}"],
                    synapse_lessons=synapse_lessons,
                    integrity_status=integrity,
                    affective_context=affective_state # Faz 12.3: Duygusal bağlam enjeksiyonu
                )
                
                # 3. Karar Verme Katmanı
                try:
                    last_decision_plan = await self.decision.decide(current_frame, last_context)
                    
                    # --- Karar Konsensüsü (Basitleştirilmiş Faz 17) ---
                    plan = last_decision_plan
                    
                    # --- Simülasyon Kapısı (Foresight Cortex Entegrasyonu) ---
                    from core.agi.cognitive.foresight_cortex import foresight_cortex
                    sim_risks = await foresight_cortex.simulate_plan(plan)
                    if sim_risks:
                        _log.info(f"Foresight: Plan simüle edildi, {len(sim_risks)} risk noktası saptandı.")

                    # 4. Hareket Katmanı (MotorSynapse - Simüle Edilmiş Yürütme) [Faz 16]
                    primary_agent = plan.steps[0].agent_id if plan.steps else "unknown"
                    
                    # --- Swarm İşbirliği Döngüsü (Phase 25) ---
                    is_swarm_eligible = current_frame.risk_level == RiskLevel.HIGH or "refactor" in plan.goal.lower() or "security" in plan.goal.lower()
                    
                    if is_swarm_eligible and primary_agent != "unknown":
                        _log.info(f"[SWARM] Karmaşık görev saptandı. Sürü İşbirliği (Swarm Cognition) başlatılıyor: {primary_agent}")
                        action_res = await self.motor_synapse.execute_plan(plan=plan, db=db, episode_id=input_id)
                        
                        if action_res.success:
                            from core.agi.cognitive.swarm_resolver import swarm_resolver
                            reviewer_id = "security" if "security" in plan.goal.lower() else "architect"
                            swarm_res = await swarm_resolver.orchestrate_peer_review(
                                producer_id=primary_agent, reviewer_id=reviewer_id,
                                task_context=current_frame.__dict__, produced_output=action_res.output_data
                            )
                            action_res.output_data = swarm_res["final_output"]
                    else:
                        action_res = await self.motor_synapse.simulate_and_execute(
                            agent_id=primary_agent, prompt=plan.goal,
                            context=last_context.__dict__ if hasattr(last_context, "__dict__") else {},
                            task_id=str(inp.input_id)
                        )
                    
                    step_output = action_res.output_data
                    is_success = action_res.success

                except (RuntimeError, Exception) as e:
                    if "tüm modeller başarısız oldu" in str(e).lower() or "rate limit" in str(e).lower():
                        _log.critical("TÜM LLM SAĞLAYICILARI DEVRE DIŞI! Yerel Failsafe moduna geçiliyor.")
                        step_output = local_failsafe.generate_reflection(current_frame.objective, "architect")
                        is_success = True  # Failsafe yanıtı döngünün devamını sağlar
                        primary_agent = "local_failsafe"
                    else:
                        raise e

                # ActionRecord formatına dönüştür (Legacy uyum)
                from core.agi.schemas import ActionRecord
                record = ActionRecord(
                    plan_id=last_decision_plan.plan_id if last_decision_plan else "failsafe",
                    step_id="step_1",
                    tool_used=primary_agent,
                    input_data=current_frame.objective,
                    output_data=step_output,
                    success=is_success,
                    timestamp=datetime.now(timezone.utc)
                )
                actions = [record]
                all_actions.extend(actions)
                cumulative_result += f"\nStep {idx+1} Output: {step_output}"

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
                
                # Nedensellik Analizi ve Otonom Öğrenme (Phase 21)
                from core.agi.adaptation.strategy_tuner import strategy_tuner
                from core.agi.adaptation.evolutionary_executor import evolutionary_executor
                from core.agi.cognitive.causal_engine import causal_engine
                
                temp_ep = EpisodeRecord(problem_frame=current_frame, actions=all_actions, verification=last_verification)
                
                # Causal Graph'ı al (Evrim için gerekli)
                causal_graph = await causal_engine.analyze_episode(temp_ep, depth=2)
                
                # Failure Learning Hook + Evolutionary Consideration (Phase 23)
                await strategy_tuner.failure_learning_hook(temp_ep)
                await evolutionary_executor.consider_evolution(temp_ep, causal_graph)
                break

        # 6. Hafıza, Öğrenme ve Metacognitive Analiz (Phase 27)
        from core.agi.cognitive.metacognition import metacognition
        
        trace_analysis = metacognition.analyze_cognitive_trace(all_actions)
        arch_drift = metacognition.check_architectural_drift()
        
        if arch_drift["drift_detected"]:
            _log.critical(f"[DRIFT] Mimari sapma saptandı: {arch_drift['missing_components']}")
            lessons_learned.append(f"Architectural DRIFT detected: {arch_drift['missing_components']}")

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
            metacognitive_score=trace_analysis["efficiency_score"],
            internal_drift_detected=arch_drift["drift_detected"],
            affective_state=affective_state, # Phase 28
            timestamp=datetime.now(timezone.utc)
        )
        episode.importance = 0.8 if last_verification and last_verification.result_status else 0.55
        
        async with session_scope() as db:
            # Theory of Mind: Modeli Kalıcı Hale Getir (Phase 22)
            from core.agi.cognitive.theory_of_mind import theory_of_mind
            await theory_of_mind.persist_state(db, str(input_id) if input_id else "global")

            if await synaptic_cortex.memory_write_gate(db, episode, "episode_record"):
                await synaptic_cortex.save_episode(db, {
                    "title": frame.objective,
                    "status": "success" if last_verification and last_verification.result_status else "failed",
                    "project_id": str(inp.input_id),
                    "final_output": str(cumulative_result)[:2000],
                    "verification_summary": getattr(last_verification, "evidence_summary", ""),
                    "lessons_learned": episode.lessons_learned,
                    "affective_state": episode.affective_state.__dict__ if episode.affective_state else None,
                    "metacognitive_score": episode.metacognitive_score
                })
                _log.info("Bölüm (Episode) hafızaya konsolide edildi.")

                # Otonom Beceri Ayrıştırma (Skill Distillation)
                if last_verification and last_verification.result_status and last_verification.integration_reality_score >= 0.7:
                    from core.agi.learning.distiller import skill_distiller
                    await skill_distiller.distill(episode, db)

                # --- [FIX-9] WorldModel Güncellemeleri ---
                # 9.3: TaskStateGraph
                try:
                    from core.agi.world.task_state_graph import task_state_graph
                    task_id = str(inp.input_id)
                    if last_verification and last_verification.result_status:
                        task_state_graph.mark_success(task_id)
                    else:
                        task_state_graph.mark_failed(
                            task_id,
                            reason=getattr(last_verification, "evidence_summary", "Unknown"),
                            causal_root=causal_graph.nodes_metadata.get("root_cause_step", "") if causal_graph else ""
                        )
                except Exception as _tsg_err:
                    _log.debug(f"TaskStateGraph güncelleme hatası: {_tsg_err}")

                # 9.4: CausalErrorGraph — başarısız episode'lardan hata örüntülerini öğren
                if causal_graph and not (last_verification and last_verification.result_status):
                    try:
                        from core.agi.world.causal_error_graph import causal_error_graph
                        causal_error_graph.ingest_causal_graph(
                            causal_graph,
                            episode_id=str(inp.input_id),
                            agent_id=str(frame.task_type.value) if frame else "system"
                        )
                    except Exception as _ceg_err:
                        _log.debug(f"CausalErrorGraph güncelleme hatası: {_ceg_err}")

                # Otonom Adaptasyon ve Politika Evrimi
                try:
                    from core.agi.adaptation.policy_engine import policy_engine
                    asyncio.create_task(policy_engine.evolve(db))
                except Exception as pe:
                    _log.warning(f"Policy evolution başlatılamadı: {pe}")
                
                # --- Otonom Politika Sentezi (Faz 18) ---
                if last_verification and last_verification.result_status:
                    from core.agi.adaptation.strategy_tuner import strategy_tuner
                    asyncio.create_task(strategy_tuner.synthesize_policy(episode))
        
        return episode

    async def _get_integrity_status(self) -> Dict[str, Any]:
        """Sistemin operasyonel dürüstlük (integrity) durumunu döner."""
        status = {
            "mode": "nominal",
            "degraded_components": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 1. Model Orkestratörü Sağlığı
        orch_health = self.model_orch.get_health_score()
        if orch_health < 0.7:
            status["mode"] = "degraded"
            status["degraded_components"].append("llm_orchestrator")
            
        # 2. Veritabanı / Failsafe Durumu
        if self.model_orch.circuit_breaker_tripped:
            status["mode"] = "failsafe"
            status["degraded_components"].append("api_availability")
            
        return status

# --- Singleton ---
central_executive = CentralExecutive()
