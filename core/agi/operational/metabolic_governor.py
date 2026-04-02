import time
import logging
from enum import Enum
from typing import Dict, List, Any, Optional
from llm.llm_types import PROVIDERS, ProviderStats, CircuitState
from core.agi.consciousness.affective_core import affective_core

_log = logging.getLogger("agi_metabolic_governor")

class MetabolicMode(str, Enum):
    TURBO  = "turbo"   # Maximum performance, highest cost models
    NORMAL = "normal"  # Balanced performance and cost
    ECO    = "eco"     # Resource conservation, cheapest models, slower pacing

class MetabolicGovernor:
    """
    Subconscious Governance (Faz 52): Sovereign Metabolism.
    Sistemin "metabolizmasını" (LLM kaynakları, gecikme, maliyet) otonom olarak yönetir.
    [Faz 48] Dinamik Ölçeklendirme ve Mode Değişimi eklendi.
    """

    def __init__(self):
        self._last_check = 0
        self._check_interval = 30 # 30 saniyede bir kontrol
        self._stress_threshold = 0.6
        self._current_mode = MetabolicMode.NORMAL
        self._metabolic_score = 1.0

    def get_mode(self) -> MetabolicMode:
        return self._current_mode

    def get_score(self) -> float:
        return self._metabolic_score

    async def update_metabolism(self, provider_map: Dict[str, ProviderStats]):
        """Sağlayıcı istatistiklerini ve duygusal durumu analiz ederek modu günceller."""
        now = time.time()
        if now - self._last_check < self._check_interval:
            return
            
        _log.debug("[METABOLISM] Metabolik tarama yapılıyor...")
        
        failures = 0
        total_latency = 0.0
        active_providers = 0
        
        for name, stats in provider_map.items():
            if stats.circuit == CircuitState.OPEN or stats.quarantine_until > now:
                failures += 1
            else:
                total_latency += stats.avg_latency
                active_providers += 1

        # 1. Sistem Stresi (Hata oranı bazlı)
        stress = failures / len(provider_map) if provider_map else 0
        
        # 2. Enerji Durumu (Affective Core)
        energy = affective_core.energy
        
        # 3. Metabolik Skor Hesapla (1.0 = Mükemmel, 0.0 = Kritik)
        # Stres puanı düşürür, Enerji puanı artırır
        self._metabolic_score = round((1.0 - stress) * 0.7 + (energy * 0.3), 2)
        
        # 4. Mod Tayini
        old_mode = self._current_mode
        if self._metabolic_score < 0.4 or energy < 0.2:
            self._current_mode = MetabolicMode.ECO
            if old_mode != MetabolicMode.ECO:
                _log.warning(f"[METABOLISM] KRİTİK: Sistem ECO moduna geçti. (Skor: {self._metabolic_score}, Enerji: {energy})")
        elif self._metabolic_score > 0.8 and energy > 0.8:
            self._current_mode = MetabolicMode.TURBO
            if old_mode != MetabolicMode.TURBO:
                _log.info(f"[METABOLISM] TURBO modu aktif: Maksimum performans çekirdeği devrede.")
        else:
            self._current_mode = MetabolicMode.NORMAL
        
        self._last_check = now

    def get_optimal_provider(self, candidates: List[str], provider_map: Dict[str, ProviderStats]) -> Optional[str]:
        """
        Anlık metabolik verilere göre en sağlıklı sağlayıcıyı seçer.
        """
        valid_candidates = []
        for name in candidates:
            p = provider_map.get(name)
            if p and p.is_available():
                valid_candidates.append(p)
        
        if not valid_candidates:
            return None
            
        # ECO modunda maliyet ve başarı oranına (health_score) daha fazla ağırlık ver
        if self._current_mode == MetabolicMode.ECO:
            # Latency'den çok başarı oranına odaklan (Failure istenmiyor)
            # Karmaşıklığı (penalty_multiplier) düşürerek daha küçük modelleri tercih et
            sorted_nodes = sorted(valid_candidates, key=lambda x: (x.health_score, -x.penalty_multiplier), reverse=True)
        else:
            sorted_nodes = sorted(valid_candidates, key=lambda x: (x.health_score, -x.avg_latency), reverse=True)
        
        return sorted_nodes[0].name

    def check_safety(self) -> Dict[str, Any]:
        """
        Sistemin operasyonel güvenliğini metabolik boyutta denetler.
        [FAZ 55] Otonom Guardrail için kritik veri sağlar.
        """
        status = "SAFE"
        if self._metabolic_score < 0.2:
            status = "DANGER"
        elif self._metabolic_score < 0.4:
            status = "WARNING"
            
        return {
            "status": status,
            "metabolic_score": self._metabolic_score,
            "mode": self._current_mode,
            "can_expand": status != "DANGER",
            "reason": "Sistem metabolik stres altında (Düşük Sağlık Skoru/Enerji)" if status != "SAFE" else "Sistem stabil"
        }

# Singleton
metabolic_governor = MetabolicGovernor()
