from abc import ABC, abstractmethod
from typing import Dict, Any
from schemas import SubtaskOutput, AgentStatus, Artifact, ArtifactType
from llm.model_orchestrator import ModelOrchestrator
from datetime import datetime, timezone
import json

class BaseAgent(ABC):
    """
    Sistemdeki tüm ajanlar bu sözleşmeye uymak ZORUNDADIR.
    """
    
    def __init__(self, orchestrator: ModelOrchestrator):
        self.llm = orchestrator
        
    @property
    @abstractmethod
    def role(self) -> str:
        """Örn: 'backend_dev', 'qa_engineer'"""
        pass
        
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Ajanın karakterini ve katı sınırlarını belirleyen prompt."""
        pass

    @abstractmethod
    async def execute(self, task_id: str, subtask_id: str, context: Dict[str, Any]) -> SubtaskOutput:
        """
        Görevi işler ve KESİNLİKLE SubtaskOutput nesnesi döner.
        Hiçbir ajan doğrudan string dönemez.
        """
        pass

    def _parse_llm_json(self, raw_content: str) -> dict:
        """LLM'den gelen metnin içindeki JSON'ı güvenli şekilde çıkarır."""
        try:
            # Markdown code block temizleme (```json ... ```)
            clean_content = raw_content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
                
            return json.loads(clean_content.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM çıktısı geçerli bir JSON değil: {e}\nRaw: {raw_content}")
