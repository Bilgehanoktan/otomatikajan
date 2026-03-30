import asyncio
from typing import List, Dict, Any, Optional
from observability.logging import get_logger

_log = get_logger("agi_theory_of_mind")

class TheoryOfMind:
    """
    Cognitive Core (Katman 30): Empathy Engine / Theory of Mind.
    Kullanıcının (USER) psikolojik ve bilişsel durumunu (Mental State) analiz eder.
    Sistemin davranışı bu model doğrultusunda (örn. 'Çok sinirli, kısa cevap ver') regüle edilir.
    """
    def __init__(self):
        self.user_state = {
            "frustration": 0.0,  # Sinir/Gerginlik (Ardışık hatalar, büyük harfler, kısa emirler)
            "urgency": 0.0,      # Acelecilik (Çok kısa promptlar, noktalama eksikliği)
            "exploration": 0.5,  # Keşif/Öğrenme (Uzun promptlar, 'nasıl' soruları)
            "analytical": 0.5    # Analitik (Kod içerikli veya yapısal promptlar)
        }
    
    def analyze_interaction(self, user_prompt: str, recent_errors: int = 0):
        """
        Kullanıcının her girdisinde onun bilişsel modelini günceller.
        """
        # 1. Uzunluk Analizi
        length = len(user_prompt)
        words = len(user_prompt.split())
        
        # 2. Sentaktik/Biçimsel Analiz (Basit)
        is_all_caps = user_prompt.isupper() and length > 4
        is_short_command = words < 5
        has_question = "?" in user_prompt
        
        # Frustration
        if recent_errors > 2 or is_all_caps:
            self.user_state["frustration"] = min(1.0, self.user_state["frustration"] + 0.3)
            self.user_state["exploration"] = max(0.0, self.user_state["exploration"] - 0.2)
        else:
            self.user_state["frustration"] = max(0.0, self.user_state["frustration"] - 0.1)
            
        # Urgency
        if is_short_command and not has_question:
            self.user_state["urgency"] = min(1.0, self.user_state["urgency"] + 0.2)
        else:
            self.user_state["urgency"] = max(0.0, self.user_state["urgency"] - 0.1)
            
        # Exploration / Analytical
        if length > 100 or has_question:
            self.user_state["exploration"] = min(1.0, self.user_state["exploration"] + 0.2)
            self.user_state["urgency"] = max(0.0, self.user_state["urgency"] - 0.1)
            
        if "def " in user_prompt or "class " in user_prompt or "import " in user_prompt:
            self.user_state["analytical"] = min(1.0, self.user_state["analytical"] + 0.2)
            
        _log.info(f"Theory of Mind: Güncel Kullanıcı Modeli: {self.get_inferred_state()}")

    def get_inferred_state(self) -> str:
        """Kullanıcının o anki en belirgin Bilişsel Modeli (Cognitive State)."""
        dominant = max(self.user_state, key=self.user_state.get)
        val = self.user_state[dominant]
        
        if val > 0.7:
            return f"Highly {dominant.capitalize()}"
        elif val > 0.4:
            return f"{dominant.capitalize()}"
        return "Neutral"

# Singleton
theory_of_mind = TheoryOfMind()
