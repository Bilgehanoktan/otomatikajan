from typing import List, Optional, Dict, Any
from packages.orchestration.agi.schemas import EpisodeRecord, AffectiveState, RiskLevel, ProblemFrame
from packages.observability.logging import get_logger

_log = get_logger("agi_motivation_engine")

class MotivationEngine:
    """
    Motivasyon Motoru (Motivation Engine).
    Sistemin içsel enerji, motivasyon ve dayanıklılık seviyelerini hesaplar.
    AGI'nin bir göreve ne kadar 'efor' harcayacağına karar verir.
    """

    def __init__(self):
        self.current_state = AffectiveState()
        from packages.orchestration.agi.consciousness.affective_core import affective_core
        self.affective = affective_core

    async def recalibrate_state(self, recent_episodes: List[Any], current_frame: ProblemFrame) -> AffectiveState:
        """
        Geçmiş deneyimlere ve mevcut göreve göre duygusal durumu yeniden kalibre eder.
        """
        _log.info("[MOTIVATION] Duygusal durum yeniden kalibre ediliyor...")
        
        # 1. Başarı Oranı Analizi (Success Rate)
        if not recent_episodes:
            success_rate = 1.0
            avg_importance = 0.5
        else:
            def _get_val(obj, key, default):
                if hasattr(obj, key): return getattr(obj, key)
                if isinstance(obj, dict): return obj.get(key, default)
                return default

            successes = [e for e in recent_episodes if _get_val(e, "success", True)]
            success_rate = len(successes) / len(recent_episodes)
            
            # Faz 12.4: Önem Analizi
            importances = [_get_val(e, "importance", 0.5) for e in recent_episodes]
            avg_importance = sum(importances) / len(recent_episodes)

        # 2. Motivasyon Seviyesi Güncelleme (Önem Ağırlıklı)
        self.current_state.motivation_level = 0.5 + (success_rate * 0.4) + (avg_importance * 0.1)

        # 3. Dayanıklılık (Resilience) Hesaplama
        # Görev KRİTİK ise sistem 'dişini sıkar' ve dayanıklılığı artırır.
        if current_frame.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            self.current_state.resilience_score = min(1.0, self.current_state.resilience_score + 0.2)
            _log.info(f"[MOTIVATION] Kritik görev! Dayanıklılık artırıldı: {self.current_state.resilience_score}")
        else:
            self.current_state.resilience_score = max(0.5, self.current_state.resilience_score - 0.05)

        # 4. Affective Core Senkronizasyonu (Phase 28)
        aff_matrix = self.affective.get_state_matrix()
        self.current_state.internal_stress = aff_matrix.get("internal_stress", 0.0)
        self.current_state.energy_reserve = aff_matrix.get("energy_reserve", 1.0)

        # 5. Israr Politikası (Persistence Policy) Belirleme
        # Stres yüksekse veya enerji düşükse 'careful' moduna geç.
        if (self.current_state.internal_stress > 0.7 or self.current_state.energy_reserve < 0.3):
            self.current_state.persistence_policy = "careful"
        elif self.current_state.motivation_level > 0.8 and self.current_state.resilience_score > 0.7:
            self.current_state.persistence_policy = "aggressive"
        else:
            self.current_state.persistence_policy = "balanced"

        # 6. Enerji Tüketimi/Geri Kazanımı (Faz 12.4)
        if success_rate > 0.8:
            # Başarılı ve önemli işler enerji verir (Dopaminerjik geri bildirim)
            self.affective.adjust_state("success", magnitude=avg_importance * 0.1)
        elif success_rate < 0.4:
            # Önemli başarısızlıklar daha fazla enerji tüketir
            self.affective.adjust_state("error", magnitude=avg_importance * 0.2)

        _log.info(f"[MOTIVATION] Yeni Durum: Policy={self.current_state.persistence_policy}, Stress={self.current_state.internal_stress:.2f}, Energy={self.current_state.energy_reserve:.2f}")
        return self.current_state

    def get_persistence_multiplier(self) -> int:
        """
        Politikaya göre 'max_attempts' çarpanı döner.
        """
        multiplier_map = {
            "careful": 1,
            "balanced": 2,
            "aggressive": 3
        }
        return multiplier_map.get(self.current_state.persistence_policy, 1)

# Singleton
motivation_engine = MotivationEngine()
