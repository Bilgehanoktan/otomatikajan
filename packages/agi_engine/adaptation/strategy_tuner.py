from datetime import datetime, timezone
from typing import Optional, Dict, Any
from packages.orchestration.agi.schemas import EpisodeRecord, RiskLevel
from llm.model_orchestrator import ModelOrchestrator
from core.agi.operational.resource_manager import resource_manager
from observability.logging import get_logger

_log = get_logger("agi_strategy_tuner")

class RuntimeStrategy:
    """Yürütme anındaki bilişsel yapılandırma."""
    def __init__(self, max_attempts: int = 3, simulation_required: bool = False, consensus_required: bool = False):
        self.max_attempts = max_attempts
        self.simulation_required = simulation_required
        self.consensus_required = consensus_required

class StrategyTuner:
    """
    Adaptation / Learning Core (Katman 7): Meta-Strategy.
    Görevin özelliklerine göre 'Düşünme Stratejisini' otonom ayarlar.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def determine_strategy(self, episode_history: list, current_frame: Any, budget_limited: bool = False, sensory_metrics: Optional[Dict[str, Any]] = None, failed_attempts: int = 0) -> RuntimeStrategy:
        """
        Geçmiş verilere ve mevcut problem çerçevesine göre strateji belirler.
        Faz 83: Dynamic Escalation - Başarısızlık durumunda strateji anlık ağırlaştırılır.
        """
        objective_text = getattr(current_frame, "objective", getattr(current_frame, "prompt", "Unknown"))
        _log.info(f"Otonom Strateji Belirleniyor: {objective_text[:50]}... (Hata Sayısı: {failed_attempts})")
        
        # 1. Kaynak Yönetimi (Resource Manager) Tahmini:
        await resource_manager.update_status()
        guidance = resource_manager.get_strategy_guidance()
        
        # 2. Sinir Sistemi (Nervous System) Stres Analizi:
        if (sensory_metrics and sensory_metrics.get("status") == "stressed") or guidance["mode"] == "CRITICAL_SAVING":
            _log.warning(f"SİSTEM KISITLI (Stres/Kaynak)! '{guidance['mode']}' aktif ediliyor.")
            return RuntimeStrategy(max_attempts=1, simulation_required=False, consensus_required=False)

        # 3. Bütçe ve Kaynak Rehberliği Uygulama
        max_attempts = 3
        if guidance["mode"] == "CONSERVATIVE" or budget_limited:
            _log.warning(f"Kısıtlı kaynak stratejisi: {guidance['mode']}")
            max_attempts = 2

        # 4. Temel Kurallar (Hard-coded Policies)
        if current_frame.risk_level == RiskLevel.CRITICAL and guidance["mode"] == "OPTIMAL":
            return RuntimeStrategy(max_attempts=5, simulation_required=True, consensus_required=True)
            
        if current_frame.risk_level == RiskLevel.HIGH and guidance["mode"] != "CRITICAL_SAVING":
            return RuntimeStrategy(max_attempts=4, simulation_required=True)
            
        # 5. Dinamik Analiz / Escalation (Faz 83)
        if failed_attempts >= 2:
            _log.warning(f"GÖREV TAKILDI ({failed_attempts} hata). STRATEJİK ESCALATION AKTİF!")
            return RuntimeStrategy(max_attempts=max_attempts + 2, simulation_required=True, consensus_required=True)
            
        return RuntimeStrategy(max_attempts=max_attempts)

    async def synthesize_policy(self, episode: EpisodeRecord):
        """
        Başarılı veya kritik başarısızlık içeren bölümlerden (Episodes) 
        yeni operasyonel POLİTİKALAR üretir. [Faz 18]
        """
        if not episode.actions and not episode.problem_frame:
             return
             
        _log.info(f"Otonom Politika Sentezi Başlatılıyor (Episode ID: {id(episode)})")
        
        prompt = f"""
        Aşağıdaki Görev Çözümünü (Episode) analiz et ve sistemin gelecekteki benzer durumlarda 
        nasıl davranması gerektiğine dair genel bir "POLİTİKA" (Policy/Guardrail) sentezle.
        
        GÖREV: {episode.problem_frame.objective if episode.problem_frame else 'N/A'}
        SONUÇ: {'Başarılı' if episode.verification and episode.verification.result_status else 'Başarısız'}
        ÖĞRENİLEN DERSLER: {episode.lessons_learned}
        
        Lütfen sentezlenen politikayı şu formatta ver:
        POLİTİKA_ADI: [Kısa_Yılan_Durum_İsmi]
        TANIM: [Kural açıklaması]
        KOŞUL: [Hangi durumda uygulanmalı]
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Politika Sentezleyicisisin. Deneyimlerden soyut kurallar çıkarırsın."
            )
            
            # Politikayı kalıcı hale getir (Bilişsel Sinaps'a Kaydet)
            from core.agi.cognitive.synaptic_cortex import synaptic_cortex as memory_store
            from db.session import session_scope
            
            async with session_scope() as db:
                await memory_store.save_policy(db, {
                    "proposed_rule": response.content,
                    "episode_id": str(id(episode)),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            _log.info(f"YENİ POLİTİKA SENTEZLENDİ VE SİNAPS'A KAYDEDİLDİ: {response.content[:100]}...")
            return response.content
        except Exception as e:
            _log.error(f"Policy synthesis failed: {e}")
            return None

    async def failure_learning_hook(self, episode: EpisodeRecord):
        """
        [Phase 21] Başarısızlık anında tetiklenen derin öğrenme ve adaptasyon kancası.
        Nedensel analiz (Causal Analysis) yapar ve stratejiyi günceller.
        """
        _log.warning(f"FAILURE LEARNING HOOK tetiklendi: {episode.episode_id}")
        
        from core.agi.cognitive.causal_engine import causal_engine
        
        # 1. Derin Nedensellik Analizi (Recursive Depth: 2)
        causal_graph = await causal_engine.analyze_episode(episode, depth=2)
        
        # 2. Karşı-Olgusal Düşünce (Counterfactual) - Alternatif ne olabilirdi?
        # Başarısızlık özetinden bir alternatif üretip simüle et.
        best_fail_step = causal_graph.nodes_metadata.get("root_cause_step")
        if best_fail_step:
            alternative = f"{best_fail_step} yerine daha muhafazakar bir yaklaşım denemek."
            sim_result = await causal_engine.simulate_counterfactual(episode, alternative)
            _log.info(f"Counterfactual Simülasyon: {sim_result.get('predicted_outcome')} (Confidence: {sim_result.get('confidence')})")
        
        # 3. Yeni Politika Sentezle
        await self.synthesize_policy(episode)

# Singleton
strategy_tuner = StrategyTuner()
