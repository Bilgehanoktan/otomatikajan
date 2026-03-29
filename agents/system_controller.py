from .base import BaseAgent
from schemas import SubtaskOutput, AgentStatus, Artifact, ArtifactType, ErrorDetail
from typing import Dict, Any
from datetime import datetime, timezone
import traceback

class SystemControllerAgent(BaseAgent):
    """
    Sistemin genel sağlığını, model performanslarını ve maliyetlerini izleyen denetleyici ajan.
    'Otomasyon' projesindeki SystemController konseptinin 'faz12' uyarlamasıdır.
    """
    
    def __init__(self, orchestrator=None):
        self.llm = orchestrator
        self.id = "system_controller"
        self.name = "Sistem Denetleyicisi"
        self.emoji = "🛡️"
    
    @property
    def role(self) -> str:
        return "system_controller"
        
    @property
    def system_prompt(self) -> str:
        return """Sen AI Şirketinin Sistem Denetleyicisisin (System Controller).
Görevin, sistemin genel sağlığını, model performanslarını ve maliyetlerini izlemektir.
Sana verilen istatistikleri incele ve aşağıdaki konularda kararlar al:
1. Hangi modeller şu an verimli çalışıyor?
2. Hangi sağlayıcılar (GPT, Claude, Gemini) sorunlu veya yavaş?
3. Genel sistem stratejisi ne olmalı? (Örn: "Maliyet çok yüksek, Gemini'ye geçelim" veya "Hata oranı arttı, sadece GPT-4 kullanalım")

Çıktıyı SADECE aşağıdaki JSON formatında ver, başka hiçbir metin ekleme:
{
  "summary": "Sistem sağlığı ve performans özeti",
  "recommendations": ["öneri 1", "öneri 2"],
  "system_status": "healthy | degraded | critical",
  "global_overrides": {"preferred_provider": "openai | anthropic | gemini | auto"} 
}"""

    async def execute(self, task_id: str, subtask_id: str, context: Dict[str, Any]) -> SubtaskOutput:
        start_time = datetime.now(timezone.utc)
        
        # 1. Orchestrator'dan güncel canlı istatistikleri al (Latency, Success Rate vb.)
        if not self.llm:
             return SubtaskOutput(
                task_id=task_id, subtask_id=subtask_id, agent_id=self.role,
                status=AgentStatus.FAILED, summary="LLM/Orchestrator atanmamış.",
                started_at=start_time, completed_at=datetime.now(timezone.utc)
            )
            
        stats = self.llm.provider_stats()
        user_prompt = f"Güncel Sistem İstatistikleri (Dinamik): {stats}\nEk Bağlam: {context.get('additional_context', 'Yok')}"
        
        try:
            # 2. Denetleme isteğini LLM'e gönder
            llm_response = await self.llm.complete_task(
                agent_role=self.role,
                prompt=user_prompt,
                system_prompt=self.system_prompt,
                task_id=task_id
            )
            
            # 3. Yanıtı JSON olarak işle
            parsed_data = self._parse_llm_json(llm_response.content)
            
            # 4. Standart çıktı formatına dönüştür
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
                summary=parsed_data.get("summary", "Sistem denetimi ve sağlık kontrolü tamamlandı."),
                raw_output=llm_response.content,
                artifacts=[
                    Artifact(
                        name="system_health_report.json", 
                        type=ArtifactType.JSON, 
                        content=llm_response.content
                    )
                ],
                started_at=start_time,
                completed_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            # 5. Hata durumunda kurtarma bilgisiyle birlikte dön
            return SubtaskOutput(
                task_id=task_id,
                subtask_id=subtask_id,
                agent_id=self.role,
                provider="unknown",
                model="unknown",
                status=AgentStatus.FAILED,
                summary=f"Sistem denetleyicisi çalışırken hata oluştu: {str(e)}",
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
