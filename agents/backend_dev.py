from .base import BaseAgent
from schemas import SubtaskOutput, AgentStatus, Artifact, ArtifactType
from typing import Dict, Any
from datetime import datetime, timezone
import traceback

class BackendDevAgent(BaseAgent):
    
    @property
    def role(self) -> str:
        return "backend_dev"
        
    @property
    def system_prompt(self) -> str:
        return """Sen kıdemli bir Backend (FastAPI/Python) geliştiricisisin.
Senden istenen görevleri yerine getir ve çıktıyı SADECE aşağıdaki JSON formatında ver, başka hiçbir açıklama ekleme:
{
  "summary": "Ne yaptığını anlatan kısa özet",
  "files": [
    {"name": "main.py", "content": "kod buraya"}
  ]
}"""

    async def execute(self, task_id: str, subtask_id: str, context: Dict[str, Any]) -> SubtaskOutput:
        start_time = datetime.now(timezone.utc)
        
        # 1. Orchestrator'dan gelen context'i prompt'a çevir
        user_prompt = f"Gereksinimler: {context.get('requirements')}\nMimari Plan: {context.get('architecture_plan')}"
        
        try:
            # 2. ModelOrchestrator üzerinden (güvenli, fallback'li) LLM'i çağır
            llm_response = await self.llm.complete_task(
                agent_role=self.role,
                prompt=user_prompt,
                system_prompt=self.system_prompt,
                task_id=task_id
            )
            
            # 3. LLM çıktısını zorunlu JSON'a parse et
            parsed_data = self._parse_llm_json(llm_response.content)
            
            # 4. Artifact (Dosya) nesnelerini oluştur
            artifacts = []
            for f in parsed_data.get("files", []):
                artifacts.append(Artifact(
                    name=f["name"],
                    type=ArtifactType.CODE,
                    content=f["content"]
                ))
                
            # 5. Başarılı Canonical Şemayı dön (Orkestratörün tam istediği format)
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
                summary=parsed_data.get("summary", "Backend kodlaması tamamlandı."),
                raw_output=llm_response.content,
                artifacts=artifacts,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            # 6. Hata durumunda da Canonical Şemayı dön (Asla çıplak Exception fırlatma, Self-Healing'e bırak)
            return SubtaskOutput(
                task_id=task_id,
                subtask_id=subtask_id,
                agent_id=self.role,
                provider="unknown",
                model="unknown",
                status=AgentStatus.FAILED,
                summary="Ajan yürütme sırasında kritik bir hata aldı.",
                raw_output="",
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                error={
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                    "is_recoverable": True
                }
            )
