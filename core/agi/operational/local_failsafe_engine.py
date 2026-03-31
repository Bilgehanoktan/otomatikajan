"""
Local Failsafe Engine - AGI Yerel Akıl Yürütme Birimi (Faz 27)
API erişimi tamamen kesildiğinde, sistemin donmasını önleyen, 
kural tabanlı ve şablon bazlı temel 'düşünce' motoru.
"""
from typing import Dict, Any, List
import re
from observability.logging import get_logger

logger = get_logger("agi_local_failsafe")

class LocalFailsafeEngine:
    def __init__(self):
        # Temel 'akıllı' şablonlar
        self.reflex_patterns = {
            r"(?i)kod.*hata|error.*code": "Yerel Analiz: Kod hatası tespit edildi. Sözdizimi kontrolü ve bağımlılık doğrulaması öneriliyor.",
            r"(?i)yeni.*dosya|create.*file": "Yerel Analiz: Dosya oluşturma isteği. Dosya yolunun geçerliliği ve izinler kontrol edilmeli.",
            r"(?i)test.*çalıştır|run.*test": "Yerel Analiz: Test yürütme isteği. Gerekli kütüphanelerin yüklü olduğundan emin olun.",
            r"(?i)strateji|plan": "Yerel Analiz: Stratejik planlama isteği. Mevcut kaynaklara göre adım adım ilerleme tavsiye edilir."
        }

    def generate_reflection(self, prompt: str, agent_role: str) -> str:
        """API'siz durumda temel bir 'yansıma' (reflection) üretir."""
        logger.info(f"Yerel Failsafe Engine devreye girdi (Rol: {agent_role})")
        
        matches = []
        for pattern, response in self.reflex_patterns.items():
            if re.search(pattern, prompt):
                matches.append(response)
        
        if not matches:
            summary = f"Yerel Analiz: '{agent_role}' rolü için genel bir sistem yanıtı. API erişimi şu an kısıtlı olduğundan derinlemesine analiz yapılamıyor, ancak operasyonel süreklilik korunuyor."
        else:
            summary = "\n".join(matches)
            
        return f"""[DEGRADED MODE - OFFLINE REASONING]
{summary}

NOT: Bu yanıt yerel failsafe motoru tarafından üretilmiştir. API bağlantısı sağlandığında daha derinlemesine analiz yapılacaktır."""

    async def execute_simulated_cycle(self, objective: str) -> Dict[str, Any]:
        """Bir düşünce döngüsünü yerel olarak simüle eder."""
        return {
            "success": True,
            "reasoning": f"Simüle edilmiş döngü: {objective} hedefi yerel kurallar çerçevesinde değerlendirildi.",
            "next_step": "Gereksinimleri yerel dosyalar üzerinden doğrula."
        }

local_failsafe = LocalFailsafeEngine()
