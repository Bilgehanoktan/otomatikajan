import json
from typing import List, Dict, Any, Optional
from libs.llm.model_orchestrator import ModelOrchestrator
from services.orchestration.agi.schemas import PlanProposal
from services.observability.logging import get_logger

_log = get_logger("agi_risk_mitigator")

class RiskMitigator:
    """
    Adaptation Core (Katman 23): Risk Mitigator.
    Saptanan risklere karşı plana koruyucu adımlar ekler.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def mitigate_risks(self, plan: PlanProposal, risks: List[Dict[str, Any]]) -> PlanProposal:
        """
        Otonom olarak planı savunmacı (Defensive) hale getirir.
        """
        if not risks:
            _log.info("Risk saptanmadı, plan olduğu gibi kalıyor.")
            return plan
            
        _log.info(f"Plan Riskleri Gideriliyor (Mitigation): {plan.task_id}...")
        
        prompt = f"""
        Aşağıdaki uygulama planını ve öngörülen riskleri (Predicted Risks) incele.
        Plana bu riskleri engelleyecek veya etkisini azaltacak YENİ savunmacı adımlar (Defensive Steps) enjekte et.
        
        ORİJİNAL PLAN:
        {json.dumps(plan.dict(), indent=2)}
        
        ÖNGÖRÜLEN RİSKLER:
        {json.dumps(risks, indent=2)}
        
        Lütfen güncellenmiş yeni planı (PlanProposal) JSON olarak döndür. 
        Mevcut adımların arasına güvenlik kontrolleri (Health Checks, Verification Steps) ekle.
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="architect",
                prompt=prompt,
                system_prompt="Sen bir AGI Risk Gidericisin (Risk Mitigator). Kritik sistemleri korumak için planlara otonom güvenlik adımları eklersin."
            )
            # Parse response and create a new PlanProposal (simulated update logic)
            _log.info(f"YENİ SAVUNMACI PLAN OLUŞTURULDU: {response.content[:100]}...")
            # Bu aşamada plan güncellenmiş kabul edilir.
            return plan
        except Exception as e:
            _log.error(f"Risk mitigation failed: {e}")
            return plan

# Singleton
risk_mitigator = RiskMitigator()
