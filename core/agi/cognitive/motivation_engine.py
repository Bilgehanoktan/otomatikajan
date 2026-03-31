from typing import List, Optional, Dict, Any
from core.agi.schemas import EpisodeRecord, AffectiveState, RiskLevel, ProblemFrame
from observability.logging import get_logger

_log = get_logger("agi_motivation_engine")

class MotivationEngine:
    """
    Motivasyon Motoru (Motivation Engine).
    Sistemin içsel enerji, motivasyon ve dayanıklılık seviyelerini hesaplar.
    AGI'nin bir göreve ne kadar 'efor' harcayacağına karar verir.
    """

    def __init__(self):
        self.current_state = AffectiveState()

    async def recalibrate_state(self, recent_episodes: List[Any], current_frame: ProblemFrame) -> AffectiveState:
        """
        Geçmiş deneyimlere ve mevcut göreve göre duygusal durumu yeniden kalibre eder.
        """
        _log.info("[MOTIVATION] Duygusal durum yeniden kalibre ediliyor...")
        
        # 1. Başarı Oranı Analizi (Success Rate)
        if not recent_episodes:
            success_rate = 1.0
        else:
            successes = [e for e in recent_episodes if getattr(e, "success", True) or (e.verification and e.verification.result_status)]
            success_rate = len(successes) / len(recent_episodes)

        # 2. Motivasyon Seviyesi Güncelleme
        # Üst üste başarı motivasyonu artırır, başarısızlık 'mood'u düşürür.
        self.current_state.motivation_level = 0.5 + (success_rate * 0.5)

        # 3. Dayanıklılık (Resilience) Hesaplama
        # Görev KRİTİK ise sistem 'dişini sıkar' ve dayanıklılığı artırır.
        if current_frame.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            self.current_state.resilience_score = min(1.0, self.current_state.resilience_score + 0.2)
            _log.info(f"[MOTIVATION] Kritik görev! Dayanıklılık artırıldı: {self.current_state.resilience_score}")
        else:
            self.current_state.resilience_score = max(0.5, self.current_state.resilience_score - 0.05)

        # 4. Israr Politikası (Persistence Policy) Belirleme
        if self.current_state.motivation_level > 0.8 and self.current_state.resilience_score > 0.7:
            self.current_state.persistence_policy = "aggressive"
        elif self.current_state.motivation_level < 0.4:
            self.current_state.persistence_policy = "careful"
        else:
            self.current_state.persistence_policy = "balanced"

        _log.info(f"[MOTIVATION] Yeni Durum: Policy={self.current_state.persistence_policy}, Motivation={self.current_state.motivation_level:.2f}")
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
