from abc import ABC, abstractmethod
from typing import Dict, Any
from libs.contracts.schemas import SubtaskOutput, AgentStatus, Artifact, ArtifactType
from libs.llm.model_orchestrator import ModelOrchestrator
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
    async def execute(self, task_id: str, subtask_id: str, prompt: str, context: Dict[str, Any]) -> SubtaskOutput:
        """
        Görevi işler ve KESİNLİKLE SubtaskOutput nesnesi döner.
        Hiçbir ajan doğrudan string dönemez.
        """
        pass

    def _build_cognitive_context(self, context: Dict[str, Any]) -> str:
        """
        Faz 12.3: Tüm ajanlar için standart 'Bilişsel Bağlam' bloğu oluşturur.
        Bu blok; Çapalar (Anchors), Kısıtlar (Inhibitions) ve Paylaşılan Belleği (State) içerir.
        """
        sections = []
        
        # 1. Causal Anchors (Önceki başarılı adımların özeti)
        anchors = context.get("causal_anchors")
        if anchors:
            sections.append(f"### ÖNCEKİ ADIMLARIN ÖZETİ (CAUSAL ANCHORS):\n{anchors}")
            
        # 2. Inhibition Signals (Kritik kısıtlar ve dersler)
        inhibitions = context.get("inhibition_signals")
        if inhibitions:
            sections.append(f"### KRİTİK KISITLAMALAR VE UYARILAR (INHIBITIONS):\n{inhibitions}")
            
        # 3. Shared State (Blackboard)
        state = context.get("shared_state")
        if state:
            sections.append(f"### PAYLAŞILAN SİSTEM BELLEĞİ (SHARED STATE):\n{json.dumps(state, indent=2)}")
            
        # 4. Consensus Data (Konsey Kararları)
        consensus = context.get("consensus_data")
        if consensus:
            sections.append(f"### KONSEY MÜNAZARASI VE KARARI:\n{consensus}")

        # 5. Long-Horizon Memory (Geçmiş Deneyimler ve Hükümler - UGC V5)
        memory_ctx = context.get("working_memory")
        if isinstance(memory_ctx, dict):
            provisos = memory_ctx.get("historical_provisos")
            if provisos:
                sections.append(f"### SİSTEM HAFIZASINDAN GELEN DERİN BİLGELİK (HISTORICAL PROVISOS):\n" + "\n".join(provisos))
            
            # General Blackboard Context for this Task
            blackboard_ctx = memory_ctx.get("blackboard")
            if blackboard_ctx:
                sections.append(f"### BLACKBOARD GÖREV BAĞLAMI:\n{json.dumps(blackboard_ctx, indent=2)}")

        if not sections:
            return ""
            
        return "\n\n" + "\n\n".join(sections) + "\n\n"

    async def _reflective_correction(self, task_prompt: str, initial_output: str, context: Dict[str, Any]) -> str:
        """
        Faz 74: Ajanın ürettiği çıktıyı kendi kendine denetlemesi.
        Eğer çıktı 'Historical Provisos' kısıtlarını ihlal ediyorsa otonom revizyon yapar.
        """
        memory_ctx = context.get("working_memory", {})
        provisos = memory_ctx.get("historical_provisos")
        
        if not provisos:
            return initial_output # Denetlenecek geçmiş kısıt yoksa orjinal çıktıyı dön
            
        audit_prompt = f"""
        Kendi ürettiğin çıktıyı denetle (Self-Audit).
        
        GÖREV: {task_prompt}
        GEÇMİŞTEN GELEN KRİTİK KISITLAR (MUST COMPLY):
        {json.dumps(provisos, indent=2)}
        
        SENİN ÜRETTİĞİN ÇIKTI:
        {initial_output}
        
        Denetim Soruları:
        1. Ürettiğin çıktı geçmiş kısıtları ihlal ediyor mu?
        2. Çıktı teknik olarak güvenli mi?
        
        Eğer sorun varsa 'REVISED_OUTPUT: ...' formatında geliştirilmiş haliyle yaz.
        Eğer sorun yoksa sadece 'PASSED' yaz.
        """
        
        try:
            audit_res = await self.llm.complete_task(
                agent_role=self.role,
                prompt=audit_prompt,
                system_prompt=f"Sen bir Öz-Denetleme (Reflective Reasoning) motorusun. Hatalarından ders alarak çıktını mükemmelleştirirsin. Rolün: {self.role}"
            )
            
            if "REVISED_OUTPUT:" in audit_res.content:
                revised = audit_res.content.split("REVISED_OUTPUT:")[1].strip()
                return revised
            return initial_output
        except Exception:
            return initial_output

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
