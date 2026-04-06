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

    async def execute(self, task_id: str, subtask_id: str, prompt: str, context: Dict[str, Any]) -> SubtaskOutput:
        start_time = datetime.now(timezone.utc)
        
        # 1. Bilişsel Bağlamı İnşa Et (Faz 12.3: Causal Continuity)
        cognitive_block = self._build_cognitive_context(context)
        
        user_prompt = f"""
 TALİMAT: {prompt}
 
 {cognitive_block}
 
 ANA HEDEFLER VE BAĞLAM:
 {context.get('parent_goal', 'Belirtilmedi')}
 """
        
        try:
            # 2. ModelOrchestrator üzerinden (güvenli, fallback'li) LLM'i çağır
            llm_response = await self.packages.llm_gateway.complete_task(
                agent_role=self.role,
                prompt=user_prompt,
                system_prompt=self.system_prompt,
                task_id=task_id
            )
            
            # 2.1 Faz 75: Reflective Reasoning (Self-Correction)
            # Ajan ürettiği ilk çıktıyı geçmiş kısıtlara göre denetler.
            _log.info(f"[SOVEREIGN-REFLECTION] Ajan {self.role} öz-denetim yapıyor...")
            final_content = await self._reflective_correction(
                task_prompt=prompt,
                initial_output=llm_response.content,
                context=context
            )
            
            # 3. Denetlenmiş LLM çıktısını zorunlu JSON'a parse et
            parsed_data = self._parse_llm_json(final_content)
            
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
