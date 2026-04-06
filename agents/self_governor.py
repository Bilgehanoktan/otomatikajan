from .base import BaseAgent
from schemas import SubtaskOutput, AgentStatus, Artifact, ArtifactType, ErrorDetail
from typing import Dict, Any
from datetime import datetime, timezone
import traceback
import logging

_log = logging.getLogger("self_governor")

class SelfGovernorAgent(BaseAgent):
    """
    Sistemin genel sağlığını, model performanslarını ve operasyonel politikalarını (Policy) 
    yöneten otonom denetleyici ajan. AGI Gap: Reflective Reasoning & Failure Learning.
    """
    
    def __init__(self, orchestrator=None):
        self.llm = orchestrator
        self.id = "self_governor" 
        self.name = "Öz-Yönetim Denetçisi (Self-Governor)"
        self.emoji = "⚖️"
    
    @property
    def role(self) -> str:
        return "self_governor"
        
    @property
    def system_prompt(self) -> str:
        return """Sen AI Şirketinin Öz-Yönetim Denetçisisin (Self-Governor).
Görevin, sistemin sadece sağlığını değil, aynı zamanda etik, maliyet ve verimlilik 
politikalarına uygunluğunu denetlemektir. 

AGI DÜZEYİ DENETİM PRENSİPLERİ:
1. Yansıtıcı Muhakeme (Reflective Reasoning): Neden hata alıyoruz? Semptom yerine kök nedene odaklan.
2. Hata Öğrenme (Failure Learning): Tekrarlayan model hatalarını (429, 400 vb.) tespit et ve karantina öner.
3. Kaynak Optimizasyonu: En iyi performansı veren modeli en düşük maliyetle seçmek için strateji belirle.

Sana verilen istatistikleri ve olay loglarını incele.
Çıktıyı SADECE aşağıdaki JSON formatında ver, başka hiçbir metin ekleme:
{
  "summary": "Sistem sağlığı ve politika uygunluk özeti",
  "reasoning": "Hataların ve performansın derinlemesine analizi (Kök neden tespiti)",
  "recommendations": ["öneri 1", "öneri 2"],
  "system_status": "healthy | degraded | critical",
  "policy_overrides": {
      "preferred_provider": "openai | anthropic | gemini | auto",
      "emergency_mode": true | false,
      "quarantine_providers": ["liste"]
  } 
}"""

    async def execute(self, task_id: str, subtask_id: str, prompt: str, context: Dict[str, Any]) -> SubtaskOutput:
        start_time = datetime.now(timezone.utc)
        
        # Faz 12.3: Bilişsel Bağlamı İnşa Et
        cognitive_block = self._build_cognitive_context(context)
        
        if not self.llm:
             return SubtaskOutput(
                task_id=task_id, subtask_id=subtask_id, agent_id=self.role,
                status=AgentStatus.FAILED, summary="LLM/Orchestrator atanmamış.",
                started_at=start_time, completed_at=datetime.now(timezone.utc)
            )
            
        # 1. Canlı İstatistikler ve Olay Loglarını Topla
        stats = self.packages.llm_gateway.provider_stats()
        
        # 2. Son Hataları DB'den Çek (AGI: State Awareness)
        recent_errors = []
        try:
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repositories.repository import EventLogRepository
            async with AsyncSessionLocal() as db:
                logs = await EventLogRepository.recent(db, n=20)
                recent_errors = [f"[{l.severity}] {l.message}" for l in logs if l.severity in ("warning", "critical")]
        except Exception as ex:
            _log.warning(f"Self-Governor DB log çekemedi: {ex}")

        user_prompt = f"""### TALİMAT
{prompt}

### GÜNCEL SİSTEM DURUMU
İstatistikler: {stats}
Son Kritik Olaylar: {recent_errors}

{cognitive_block}

### BAĞLAM
Görev Tanımı: {context.get('requirements', 'Periyodik Sistem Denetimi')}
Ek Bilgi: {context.get('additional_context', 'Yok')}

Lütfen kök neden analizi yaparak sistem politikalarını güncelle."""
        
        try:
            # 3. Muhakeme ve Karar Süreci
            llm_response = await self.packages.llm_gateway.complete_task(
                agent_role=self.role,
                prompt=user_prompt,
                system_prompt=self.system_prompt,
                task_id=task_id
            )
            
            # 4. Yanıtı JSON olarak işle
            parsed_data = self._parse_llm_json(llm_response.content)
            
            # 5. Başarı durumunu ve AGI kanıtlarını kaydet
            return SubtaskOutput(
                task_id=task_id,
                subtask_id=subtask_id,
                agent_id=self.role,
                provider=llm_response.provider,
                model=llm_response.model_name,
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
                cost_usd=llm_response.cost_usd,
                latency_s=llm_response.latency_s,
                status=AgentStatus.SUCCESS,
                summary=parsed_data.get("summary", "Sistem öz-yönetim denetimi tamamlandı."),
                raw_output=llm_response.content,
                artifacts=[
                    Artifact(
                        name="governance_policy_update.json", 
                        type=ArtifactType.JSON, 
                        content=llm_response.content
                    )
                ],
                started_at=start_time,
                completed_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            _log.error(f"Self-Governor Kritik Hata: {str(e)}")
            return SubtaskOutput(
                task_id=task_id,
                subtask_id=subtask_id,
                agent_id=self.role,
                status=AgentStatus.FAILED,
                summary=f"Öz-Yönetim Denetçisi hatası: {str(e)}",
                raw_output="",
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                error=ErrorDetail(
                    error_type=type(e).__name__,
                    message=str(e),
                    traceback=traceback.format_exc(),
                    is_recoverable=True
                )
            )
