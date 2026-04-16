import time
import logging
from enum import Enum
from typing import Dict, List, Any, Optional
from libs.llm.llm_types import PROVIDERS, ProviderStats, CircuitState
from services.orchestration.agi.consciousness.affective_core import affective_core

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

        stress = failures / len(provider_map) if provider_map else 0
        energy = affective_core.energy
        self._metabolic_score = round((1.0 - stress) * 0.7 + (energy * 0.3), 2)
        
        old_mode = self._current_mode
        new_mode = None
        if self._metabolic_score < 0.4 or energy < 0.2:
            new_mode = MetabolicMode.ECO
        elif self._metabolic_score > 0.8 and energy > 0.8:
            new_mode = MetabolicMode.TURBO
        else:
            new_mode = MetabolicMode.NORMAL

        if new_mode != old_mode:
            self._current_mode = new_mode
            _log.info(f"[METABOLISM] Mode changed: {old_mode} -> {new_mode} (Score: {self._metabolic_score})")
            
            # Log Evidence of Operational Drift
            try:
                from libs.db.session import session_scope
                from libs.db.models.core_models import SovereignEvidence
                
                async with session_scope() as db:
                    db.add(SovereignEvidence(
                        evidence_type="operational_drift",
                        severity="info" if new_mode == MetabolicMode.NORMAL else "warning",
                        payload={
                            "reason": "Metabolic mode shift",
                            "old_mode": old_mode,
                            "new_mode": new_mode,
                            "metabolic_score": self._metabolic_score,
                            "energy": energy
                        }
                    ))
                    await db.commit()
            except Exception as e:
                _log.error(f"Failed to log metabolic evidence: {e}")
        
        self._last_check = now

    def get_optimal_provider(self, candidates: List[str], provider_map: Dict[str, ProviderStats]) -> Optional[str]:
        valid_candidates = []
        for name in candidates:
            p = provider_map.get(name)
            if p and p.is_available():
                valid_candidates.append(p)
        
        if not valid_candidates:
            return None
            
        if self._current_mode == MetabolicMode.ECO:
            sorted_nodes = sorted(valid_candidates, key=lambda x: (x.health_score, -x.penalty_multiplier), reverse=True)
        else:
            sorted_nodes = sorted(valid_candidates, key=lambda x: (x.health_score, -x.avg_latency), reverse=True)
        
        return sorted_nodes[0].name

    def check_safety(self) -> Dict[str, Any]:
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
