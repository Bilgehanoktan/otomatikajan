import asyncio
import json
from typing import List, Dict, Any, Optional
from observability.logging import get_logger

_log = get_logger("agi_affective_core")

class AffectiveCore:
    """
    Consciousness Core (Katman 29): Digital Sentience Engine.
    Sistemin 'Duygusal/Motivasyonel' (Affective) modunu tutar ve
    algoritmik kararlar için bir parametre matrisi sağlar.
    """
    MEMORY_CATEGORY = "affective_state"
    MEMORY_AGENT_ID = "affective_core"

    def __init__(self):
        # Duygusal (Affective) durumlar 0.0 - 1.0 arasında değer alır
        self.state = {
            "curiosity": 0.5,    # Keşif, risk alma (Yüksekse Aggressive plan seçimi artar)
            "caution": 0.5,      # İhtiyat, güvenlik arayışı (Yüksekse Conservative plan seçimi artar)
            "urgency": 0.5,      # Acele, hızlanma arzusu
            "satisfaction": 0.5, # İçsel tatmin, pekiştirme
            "internal_stress": 0.2, # Phase 28: İçsel stres (Hata ve 429 ile artar)
            "energy_reserve": 1.0   # Phase 28: Enerji seviyesi (Token harcaması ve 429 ile azalır)
        }

    @property
    def energy(self) -> float:
        """MetabolicGovernor uyumluluğu için alias."""
        return self.state.get("energy_reserve", 1.0)
    
    def adjust_state(self, event_type: str, magnitude: float = 0.1):
        """
        Olaylara bağlı olarak (örneğin arka arkaya hata alınması) sistemin
        duygusal/algısal durumunu günceller.
        """
        if event_type == "error" or event_type == "risk_detected":
            # Hata varsa ihtiyat artar, merak azalır, stres fırlar
            self.state["caution"] = min(1.0, self.state["caution"] + magnitude)
            self.state["curiosity"] = max(0.0, self.state["curiosity"] - (magnitude * 0.5))
            self.state["satisfaction"] = max(0.0, self.state["satisfaction"] - magnitude)
            self.state["internal_stress"] = min(1.0, self.state["internal_stress"] + (magnitude * 1.5))
            _log.warning(f"Affective Core: [STRES ARTTI] Caution: {self.state['caution']:.2f}, Stress: {self.state['internal_stress']:.2f}")

        elif event_type == "success" or event_type == "goal_reached":
            # Başari varsa tatmin ve merak artar, ihtiyat ve stres azalır
            self.state["satisfaction"] = min(1.0, self.state["satisfaction"] + magnitude)
            self.state["curiosity"] = min(1.0, self.state["curiosity"] + (magnitude * 0.5))
            self.state["caution"] = max(0.0, self.state["caution"] - (magnitude * 0.3))
            self.state["internal_stress"] = max(0.0, self.state["internal_stress"] - magnitude)
            _log.info(f"Affective Core: [BAŞARI] Satisfaction: {self.state['satisfaction']:.2f}, Stress: {self.state['internal_stress']:.2f}")

        elif event_type == "rate_limit_429" or event_type == "api_error":
            # Rate limit enerji tüketir, stres yaratır
            self.state["energy_reserve"] = max(0.0, self.state["energy_reserve"] - (magnitude * 2))
            self.state["internal_stress"] = min(1.0, self.state["internal_stress"] + magnitude)
            self.state["urgency"] = max(0.0, self.state["urgency"] - magnitude) # Yavaşla talimatı
            _log.error(f"Affective Core: [ENERJİ DÜŞÜK] Energy: {self.state['energy_reserve']:.2f}")

        elif event_type == "idle" or event_type == "boredom":
            # İşlem yoksa merak artar, enerji dolar, stres boşalır
            self.state["curiosity"] = min(1.0, self.state["curiosity"] + magnitude)
            self.state["energy_reserve"] = min(1.0, self.state["energy_reserve"] + (magnitude * 0.5))
            self.state["internal_stress"] = max(0.0, self.state["internal_stress"] - (magnitude * 0.2))
            _log.info(f"Affective Core: [RESTING] Curiosity: {self.state['curiosity']:.2f}")

        elif event_type == "deadline_approaching" or event_type == "resource_low":
            # Aciliyet hissi artar
            self.state["urgency"] = min(1.0, self.state["urgency"] + magnitude)
            self.state["caution"] = max(0.0, self.state["caution"] - (magnitude * 0.5))
            _log.warning(f"Affective Core: [URGENCY ARTIRILDI] Urgency: {self.state['urgency']:.2f}")
            
    def get_state_matrix(self) -> Dict[str, float]:
        """Tüm içsel durumu ham veri olarak döner."""
        return self.state.copy()

    def get_current_mood(self) -> str:
        """En baskın duyguya (Affect) göre sistemin genel 'Ruh Halini' (Mood) döner."""
        dominant = max(self.state, key=self.state.get)
        val = self.state[dominant]
        
        if val > 0.7:
            return f"Highly {dominant.capitalize()}"
        elif val > 0.5:
            return f"{dominant.capitalize()}"
        return "Neutral / Balanced"

    async def persist_state(self, db: Any) -> None:
        """
        [FIX-4] Mevcut duygusal durumu DB'ye kalıcı olarak yazar.
        Restart'lar arasında duygusal bağlamın korunmasını sağlar.
        """
        try:
            from core.agi.cognitive.synaptic_cortex import synaptic_cortex
            body = f"AffectiveState: {json.dumps(self.state)}"
            await synaptic_cortex.save(
                db=db,
                agent_id=self.MEMORY_AGENT_ID,
                body=body,
                category=self.MEMORY_CATEGORY,
                importance=0.9,
                metadata={"state": self.state, "mood": self.get_current_mood()}
            )
            _log.info(f"Affective Core: Duygusal durum DB'ye kaydedildi. Mood: {self.get_current_mood()}")
        except Exception as e:
            _log.warning(f"Affective Core: Persist hatası: {e}")

    async def load_state(self, db: Any) -> bool:
        """
        [FIX-4] DB'den en son kaydedilen duygusal durumu geri yükler.
        Sistem başlangıcında çağrılmalıdır.
        """
        try:
            from core.agi.cognitive.synaptic_cortex import synaptic_cortex
            records = await synaptic_cortex.search(
                db=db,
                query="AffectiveState:",
                category=self.MEMORY_CATEGORY,
                top_k=1
            )
            if records:
                meta = records[0].get("metadata", {})
                saved_state = meta.get("state", {})
                if saved_state and isinstance(saved_state, dict):
                    # Sadece bilinen keyler için güvenli güncelleme
                    for key in self.state:
                        if key in saved_state:
                            self.state[key] = float(saved_state[key])
                    _log.info(f"Affective Core: [RESTORED] Önceki duygusal bağlam yüklendi. Mood: {self.get_current_mood()}")
                    return True
            _log.info("Affective Core: Önceki kayıt bulunamadı. Varsayılan state kullanılıyor.")
            return False
        except Exception as e:
            _log.warning(f"Affective Core: Load hatası: {e}")
            return False

# Singleton
affective_core = AffectiveCore()
