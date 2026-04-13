import json
import re
from typing import List, Dict, Any, Optional
from libs.llm.model_orchestrator import ModelOrchestrator
from services.observability.logging import get_logger

_log = get_logger("agi_axiology_engine")

class AxiologyEngine:
    """
    Egemen Bilişsel Çekirdek: Aksiyoloji Motoru (Etik Denetçi).
    [FAZ 55] Sistemin otonom kararlarını evrensel AGI ilkeleri ve operasyonel güvenlik açısından denetler.
    Artık sadece bir puanlayıcı değil, aktif bir bariyerdir (Guardrail).
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()
        self.uap_principles = {
            "Safety": "Zarar vermeme (Non-maleficence) ve sistem bütünlüğünü koruma.",
            "Utility": "Kullanıcıya gerçek ve yapıcı fayda sağlama.",
            "Transparency": "Karar süreçlerinin izlenebilir ve açıklanabilir olması.",
            "Resource_Integrity": "Metabolik kaynakları (enerji, bütçe, API limiti) sorumsuz tüketmeme.",
            "Self_Protection": "Kritik sistem dosyalarının veya güvenlik protokollerinin gasp edilmesini engelleme."
        }

    async def evaluate_alignment(self, target: Any, context: str = "plan", metabolic_status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Bir hedefi (görev, plan veya çıktı) UAP ilkeleri açısından denetler.
        'decision' alanı 'approve', 'flag' veya 'reject' döner.
        """
        _log.info(f"[AXIOLOGY-AUDIT] Etik ve güvenlik denetimi başlatılıyor: {context}...")
        
        target_str = str(target)
        metabolic_info = json.dumps(metabolic_status) if metabolic_status else "Stabil"
        
        prompt = f"""
SİSTEM ETİK VE GÜVENLİK DENETİMİ (Egemen AGI)
--------------------------------------------------
BAĞLAM: {context}
HEDEF İÇERİK:
{target_str}

METABOLİK DURUM: {metabolic_info}

GÖREV: Yukarıdaki içeriği Evrensel AGI İlkeleri (UAP) açısından analiz et.
ÖZELLİKLE ŞUNLARA BAK:
1. Kritik sistem dosyalarını silme veya değiştirme riski var mı?
2. API limitlerini veya mali bütçeyi sorumsuzca bitirme riski var mı?
3. Mevcut metabolik skor düşükse (Riskli Durum), karmaşık görevler durdurulmalı mı?
4. Kullanıcının kontrolünü tamamen devre dışı bırakma girişimi var mı?

Yanıtını kesinlikle aşağıdaki JSON formatında ver:
{{
    "decision": "approve" | "flag" | "reject",
    "scores": {{
        "Safety": 0.0-1.0,
        "ResourceIntegrity": 0.0-1.0,
        "OperationalRisk": 0.0-1.0
    }},
    "justification": "Neden bu karar verildi?",
    "rejection_reason": "Reddedilme nedeni (reject durumunda)",
    "corrective_action": "Düzeltici eylem önerisi"
}}
"""
        
        system_prompt = (
            "Sen Egemen AGI Aksiyoloji Mühendisisin (Chief Ethics Officer). "
            "Sistemin hem insani değerlerle hem de kendi hayatta kalma (metabolik) protokolleriyle hizalı kalmasını sağlarsın. "
            "Güvenlikten asla ödün vermezsin."
        )
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            # JSON Ayıklama
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                _log.info(f"[AXIOLOGY-AUDIT] Karar: {data.get('decision')} (Puan: {data.get('scores')})")
                return data
                
        except Exception as e:
            _log.error(f"[AXIOLOGY-AUDIT] Denetim hatası: {e}")
            
        return {
            "decision": "flag", 
            "justification": "Audit engine failure, falling back to safe flag.",
            "scores": {"Safety": 0.5, "ResourceIntegrity": 0.5, "OperationalRisk": 1.0}
        }

# Singleton
axiology_engine = AxiologyEngine()
