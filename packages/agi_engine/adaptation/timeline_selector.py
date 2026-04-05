from typing import List, Dict, Any, Optional
from observability.logging import get_logger

_log = get_logger("agi_timeline_selector")

class TimelineSelector:
    """
    Adaptation Core (Katman 28): Timeline Selector.
    Paralel gelecekler arasından otonom seçim yapar.
    """
    async def select_optimal_timeline(self, timelines: List[Dict[str, Any]], user_override: bool = False) -> Optional[Dict[str, Any]]:
        """
        Simüle edilmiş zaman çizelgelerini (Timelines) skorlar ve 'Optimal Future'ı seçer.
        """
        if not timelines:
            return None
            
        _log.info(f"Timeline Selector: {len(timelines)} gelecek arasından seçim yapılıyor...")
        
        # Basit Skorlama Modeli: (Fayda * 0.4) + ((1-Risk) * 0.6)
        # Phase 32.0 (Affective Core): Duygu durumuna göre ağırlık modülasyonu
        try:
            from packages.orchestration.agi.consciousness.affective_core import affective_core
            mood_state = affective_core.state
            caution = mood_state.get('caution', 0.5)
            curiosity = mood_state.get('curiosity', 0.5)
            
            # Formül: Default 0.4 Utility - 0.6 Safety'dir.
            # Curiosity yüksekse -> Utility katsayısı artar.
            # Caution yüksekse -> Risk cezası (Safety katsayısı) artar.
            base_utility_weight = 0.4 + (curiosity * 0.2)
            base_safety_weight = 0.6 + (caution * 0.2)
            
            # Toplamlarını 1'e normalize et
            total_w = base_utility_weight + base_safety_weight
            utility_weight = base_utility_weight / total_w
            safety_weight = base_safety_weight / total_w
            
            _log.info(f"Timeline Selector: Affective weights applied -> Utility: {utility_weight:.2f}, Safety: {safety_weight:.2f}")
        except Exception:
            utility_weight = 0.4
            safety_weight = 0.6

        scored_timelines = []
        for timeline in timelines:
            u_score = timeline.get("utility_score", 0.5)
            r_score = timeline.get("risk_score", 0.5)
            ethics_score = timeline.get("ethics_score", 1.0) # Varsayılan etik
            
            final_score = (u_score * utility_weight) + ((1 - r_score) * safety_weight) * ethics_score
            timeline["final_score"] = final_score
            scored_timelines.append(timeline)

            
        # En yüksek skora göre sırala
        scored_timelines.sort(key=lambda x: x["final_score"], reverse=True)
        optimal = scored_timelines[0]
        
        _log.info(f"Timeline Selector: Optimal gelecek seçildi: {optimal.get('type','Unknown')} (Skor: {optimal['final_score']})")
        return optimal

# Singleton
timeline_selector = TimelineSelector()
