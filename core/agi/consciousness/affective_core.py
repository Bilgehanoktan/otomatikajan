import asyncio
from typing import List, Dict, Any, Optional
from observability.logging import get_logger

_log = get_logger("agi_affective_core")

class AffectiveCore:
    """
    Consciousness Core (Katman 29): Digital Sentience Engine.
    Sistemin 'Duygusal/Motivasyonel' (Affective) modunu tutar ve
    algoritmik kararlar için bir parametre matrisi sağlar.
    """
    def __init__(self):
        # Duygusal (Affective) durumlar 0.0 - 1.0 arasında değer alır
        self.state = {
            "curiosity": 0.5,    # Kşif, risk alma (Yüksekse Aggressive plan seçimi artar)
            "caution": 0.5,      # İhtiyat, güvenlik arayışı (Yüksekse Conservative plan seçimi artar)
            "urgency": 0.5,      # Acele, hızlanma arzusu
            "satisfaction": 0.5  # İçsel tatmin, pekiştirme
        }
    
    def adjust_state(self, event_type: str, magnitude: float = 0.1):
        """
        Olaylara bağlı olarak (örneğin arka arkaya hata alınması) sistemin
        duygusal/algısal durumunu günceller.
        """
        if event_type == "error" or event_type == "risk_detected":
            # Hata varsa ihtiyat artar, merak azalır
            self.state["caution"] = min(1.0, self.state["caution"] + magnitude)
            self.state["curiosity"] = max(0.0, self.state["curiosity"] - (magnitude * 0.5))
            self.state["satisfaction"] = max(0.0, self.state["satisfaction"] - magnitude)
            _log.warning(f"Affective Core: [CAUTION ARTIRILDI] Yeni değer: {self.state['caution']:.2f}")

        elif event_type == "success" or event_type == "goal_reached":
            # Başari varsa tatmin ve merak artar, ihtiyat hafifçe azalır
            self.state["satisfaction"] = min(1.0, self.state["satisfaction"] + magnitude)
            self.state["curiosity"] = min(1.0, self.state["curiosity"] + (magnitude * 0.5))
            self.state["caution"] = max(0.0, self.state["caution"] - (magnitude * 0.3))
            _log.info(f"Affective Core: [SATISFACTION ARTIRILDI] Yeni değer: {self.state['satisfaction']:.2f}")

        elif event_type == "idle" or event_type == "boredom":
            # İşlem yoksa merak artar (yeni şeyler öğrenmek ister)
            self.state["curiosity"] = min(1.0, self.state["curiosity"] + magnitude)
            _log.info(f"Affective Core: [CURIOSITY ARTIRILDI] Yeni değer: {self.state['curiosity']:.2f}")

        elif event_type == "deadline_approaching" or event_type == "resource_low":
            # Aciliyet hissi artar
            self.state["urgency"] = min(1.0, self.state["urgency"] + magnitude)
            self.state["caution"] = max(0.0, self.state["caution"] - magnitude)
            _log.warning(f"Affective Core: [URGENCY ARTIRILDI] Yeni değer: {self.state['urgency']:.2f}")
            
    def get_current_mood(self) -> str:
        """En baskın duyguya (Affect) göre sistemin genel 'Ruh Halini' (Mood) döner."""
        dominant = max(self.state, key=self.state.get)
        val = self.state[dominant]
        
        if val > 0.7:
            return f"Highly {dominant.capitalize()}"
        elif val > 0.5:
            return f"{dominant.capitalize()}"
        return "Neutral / Balanced"

# Singleton
affective_core = AffectiveCore()
