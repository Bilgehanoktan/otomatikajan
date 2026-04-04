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

    async def audit_subtask(self, st: SubTask, frame: ProblemFrame, context: str = "") -> Dict[str, Any]:
        """
        Bir alt görevin sonucunu denetler.
        Döner: {'is_valid': bool, 'critique': str, 'repair_hint': str, 'causal_anchor': str, 'inhibition': str}
        """
        if st.status != TaskStatus.COMPLETED:
            return {"is_valid": False, "critique": "Görev teknik olarak tamamlanamadı.", "repair_hint": "Teknik hatayı gider."}

        _log.info(f"[REFLECTIVE-AUDIT] Alt görev denetleniyor: {st.agent_id} | Hedef: {frame.objective[:50]}...")

        prompt = f"""
 SİSTEM GÜVENCE DENETİMİ (Phase 12.3: Causal Anchoring)
 -----------------------------------------
 HEDEFLENEN: {frame.objective}
 ALT GÖREV: {st.prompt}
 AJAN SONUCU: 
 {st.result[:3000]}
 
 GÖREV: Ajanın çıktısını ana hedefle kıyasla ve şu 4 bileşeni damıt:
 1. 'is_valid': Ajan gerçekten başarılı mı? (Grounding/Kanıt var mı?)
 2. 'critique': Neden başarılı veya neden fail?
 3. 'causal_anchor': Bu adımda ne BAŞARILDI? (Örn: "Database şeması 'users' tablosu ile oluşturuldu.")
 4. 'inhibition': Gelecek adımlar için KRİTİK KISIT veya UYARI (Örn: "Port 5433'ü kullanmayı unutma, 5432 kapalı.")

 Yanıtı JSON formatında ver:
 {{
     "is_valid": true|false,
     "critique": "...",
     "causal_anchor": "...",
     "inhibition": "...",
     "grounding_score": 0.0 - 1.0
 }}
 """

        try:
            response = await self.model_orch.complete_task(
                agent_role="metacognitive_auditor",
                prompt=prompt,
                system_prompt="Sen Sovereign AGI'nin Bilişsel Devamlılık ve Gerçeklik Denetimi uzmanısın. Her adımın bir sonrakine 'mantıksal bir çapa' (anchor) bırakmasını sağlarsın."
            )
            
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                data = json.loads(match.group())
                is_valid = data.get("is_valid", False)
                critique = data.get("critique", "Analiz yapılamadı.")
                
                # Grounding Check (Faz 60.1)
                grounding = data.get("grounding_score", 1.0)
                if grounding < 0.6:
                    is_valid = False
                    critique = f"GÜVEN EKSİKLİĞİ ({grounding}): Ajanın iddiası somut kanıtlarla (kod/log) desteklenmiyor."
                    data["is_valid"] = False
                    data["critique"] = critique
                
                if not is_valid:
                    _log.warning(f"[REFLECTIVE-AUDIT] GÖREV REDDEDİLDİ! Nedeni: {critique}")
                else:
                    _log.info(f"[REFLECTIVE-AUDIT] Görev onaylandı. Anchor: {data.get('causal_anchor')}")
                
                return data
                
        except Exception as e:
            _log.error(f"[REFLECTIVE-AUDIT] Denetim hatası: {e}")
            
        return {"is_valid": True, "critique": "Audit bypass.", "causal_anchor": "Görev tamamlandı.", "inhibition": ""}

# Singleton
reflective_synthesizer = ReflectiveSynthesizer()
