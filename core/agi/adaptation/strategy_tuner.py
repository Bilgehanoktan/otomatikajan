from typing import Optional, Dict, Any
from core.agi.schemas import EpisodeRecord, RiskLevel
from llm.model_orchestrator import ModelOrchestrator
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

    async def determine_strategy(self, episode_history: list, current_frame: Any, budget_limited: bool = False, sensory_metrics: Optional[Dict[str, Any]] = None) -> RuntimeStrategy:
        """
        Geçmiş verilere ve mevcut problem çerçevesine göre strateji belirler.
        Faz 18: Performans Duyarlı (Stress-Aware) strateji seçimi eklendi.
        """
        _log.info(f"Otonom Strateji Belirleniyor: {current_frame.objective[:50]}... (Bütçe Kısıtı: {budget_limited})")
        
        # 1. Sinir Sistemi (Nervous System) Stres Analizi:
        if sensory_metrics and sensory_metrics.get("status") == "stressed":
            _log.warning("SİSTEM STRES ALTINDA! 'Efficiency Mode' (Verimlilik Modu) aktif ediliyor.")
            return RuntimeStrategy(max_attempts=1, simulation_required=False, consensus_required=False)

        # 2. Bütçe Kısıtı Varsa: En ucuz ve hızlı yolu seç
        if budget_limited:
            _log.warning("Bütçe kısıtlı! Maliyet odaklı stratejiye geçildi.")
            return RuntimeStrategy(max_attempts=2, simulation_required=False, consensus_required=False)

        # 2. Temel Kurallar (Hard-coded Policies)
        if current_frame.risk_level == RiskLevel.CRITICAL:
            return RuntimeStrategy(max_attempts=5, simulation_required=True, consensus_required=True)
            
        if current_frame.risk_level == RiskLevel.HIGH:
            return RuntimeStrategy(max_attempts=4, simulation_required=True)
            
        # 3. Dinamik Analiz (LLM Optimization)
        # Geçmişteki benzer başarısızlıkları analiz edip stratejiyi ağırlaştırabiliriz.
        return RuntimeStrategy(max_attempts=3)

# Singleton
strategy_tuner = StrategyTuner()
