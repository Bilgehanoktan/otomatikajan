import json
import re
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator
from core.agi.schemas import ProblemFrame, ActionRecord, VerificationReport

_log = get_logger("agi_audit")

class AuditGate:
    """
    Güvenlik ve Denetim Çekirdek - Doğrulama Katmanı.
    Eylemleri ve çıktıları ProblemFrame kriterlerine göre denetler.
    """
    def __init__(self, model_orch: ModelOrchestrator):
        self.model_orch = model_orch

    async def verify(self, frame: ProblemFrame, actions: List[ActionRecord], final_output: Any) -> VerificationReport:
        _log.info(f"Doğrulanıyor: {frame.objective}")

        prompt = self._build_audit_prompt(frame, actions, final_output)
        try:
            response = await self.model_orch.generate(
                prompt,
                task_id=f"audit_{frame.objective[:20]}",
                preferred_agent="code_reviewer" # Verification represents review
            )
            
            audit_data = self._parse_json_from_response(response)
            
            return VerificationReport(
                result_status=audit_data.get("result_status", False),
                evidence_summary=audit_data.get("evidence_summary", "No evidence provided"),
                unresolved_risks=audit_data.get("unresolved_risks", []),
                confidence_adjusted=audit_data.get("confidence_adjusted", 0.5),
                integration_reality_score=audit_data.get("integration_reality_score", 0.0),
                safe_to_finalize=audit_data.get("safe_to_finalize", False),
                safe_to_learn=audit_data.get("safe_to_learn", False),
                followup_needed=audit_data.get("followup_needed", [])
            )
        except Exception as e:
            _log.error(f"Denetim hatası: {e}")
            return VerificationReport(result_status=False, evidence_summary=f"Audit failed: {e}")

    def _build_audit_prompt(self, frame: ProblemFrame, actions: List[ActionRecord], final_output: Any) -> str:
        action_summary = "\n".join([f"- {a.step_id}: {a.tool_used} ({'Başarılı' if a.success else 'Başarısız'})" for a in actions])
        
        return f"""
        Aşağıdaki görevin çıktılarını ve eylemlerini denetle. 
        Gerçekten işe yarayıp yaramadığını (Integration Reality) sorgula.
        
        Hedef: {frame.objective}
        Beklenen Kanıtlar: {frame.evidence_required}
        Yapılan Eylemler:
        {action_summary}
        
        Final Çıktı:
        {final_output}
        
        Yanıtı SADECE aşağıdaki JSON formatında ver:
        {{
            "result_status": true|false,
            "evidence_summary": "Kanıtların özeti",
            "unresolved_risks": ["risk 1"],
            "confidence_adjusted": 0.0-1.0,
            "integration_reality_score": 0.0-1.0 (Kod gerçekten çalışıyor mu yoksa sadece yazıldı mı?),
            "safe_to_finalize": true|false,
            "safe_to_learn": true|false (Hafızaya alınmalı mı?),
            "followup_needed": ["takip adımı 1"]
        }}
        """

    def _parse_json_from_response(self, text: str) -> Dict[str, Any]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}
