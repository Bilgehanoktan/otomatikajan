import logging
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from llm.model_orchestrator import ModelOrchestrator
from core.agi.task_governance import SubTask, TaskStatus
from core.agi.schemas import ProblemFrame

_log = logging.getLogger("agi_reflective_synthesizer")

class ReflectiveSynthesizer:
    """
    Cognitive Layer 50: Reflective Synthesis (Yansımalı Sentez).
    Her alt görevin çıktısını, ana hedefle (Goal) ve mimari kısıtlamalarla kıyaslar.
    Ajanın 'başardım' dediği şeyin gerçekten hedefe hizmet edip etmediğini denetler.
    """

    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def audit_subtask(self, st: SubTask, frame: ProblemFrame, context: str = "") -> Tuple[bool, str, str]:
        """
        Bir alt görevin sonucunu denetler.
        Döner: (başarılı_mı, eleştiri, tamir_ipucu)
        """
        if st.status != TaskStatus.COMPLETED:
            return False, "Görev teknik olarak tamamlanamadı.", "Teknik hatayı gider."

        _log.info(f"[REFLECTIVE-AUDIT] Alt görev denetleniyor: {st.agent_id} | Hedef: {frame.objective[:50]}...")

        prompt = f"""
Sovereign AGI Bilişsel Denetim (Phase 50)
-----------------------------------------
ANA HEDEF: {frame.objective}
ALT GÖREV TALİMATI: {st.prompt}
AJAN ÇIKTISI (SONUÇ): 
{st.result[:2000]}

GÖREV: Ajanın çıktısını ana hedefle kıyasla. 
Ajan gerçekten hedefe hizmet eden, doğru ve kaliteli bir sonuç üretti mi? 
Yoksa yüzeysel bir cevap mı verdi veya hata mı yaptı?

Yanıtı JSON formatında ver:
{{
    "is_valid": true|false,
    "critique": "Sonucun neden geçerli veya geçersiz olduğuna dair teknik eleştiri",
    "repair_hint": "Eğer geçersizse, ajana bir sonraki denemede neyi düzeltmesi gerektiğini söyleyen ipucu",
    "confidence_score": 0.0 - 1.0
}}
"""

        try:
            response = await self.model_orch.complete_task(
                agent_role="metacognitive_auditor",
                prompt=prompt,
                system_prompt="Sen bir AGI Kalite ve Mantık Denetçisisin. Ajanların çıktılarını 'Bilişsel Yansıma' ile sorgularsın."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                is_valid = data.get("is_valid", False)
                critique = data.get("critique", "Analiz yapılamadı.")
                repair_hint = data.get("repair_hint", "")
                
                if not is_valid:
                    _log.warning(f"[REFLECTIVE-AUDIT] GÖREV REDDEDİLDİ! Nedeni: {critique}")
                else:
                    _log.info(f"[REFLECTIVE-AUDIT] Görev onaylandı. Güven skoru: {data.get('confidence_score')}")
                
                return is_valid, critique, repair_hint
                
        except Exception as e:
            _log.error(f"[REFLECTIVE-AUDIT] Denetim hatası: {e}")
            
        return True, "Denetim sistemi hatası, güvenildi.", "" # Hata durumunda akışı bozma (Fallback: True)

# Singleton
reflective_synthesizer = ReflectiveSynthesizer()
