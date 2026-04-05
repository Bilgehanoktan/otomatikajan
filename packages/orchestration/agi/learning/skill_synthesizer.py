import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from packages.llm_gateway.model_orchestrator import ModelOrchestrator
from packages.observability.logging import get_logger
from sqlalchemy.future import select
from packages.persistence.models import Memory 

_log = get_logger("agi_skill_synthesizer")

class SkillSynthesizer:
    """
    Learning Core (Katman 17): Autonomous Externalization.
    Sistemin soyut bilgisini (Wisdom) somut becerilere (Skills) dönüştürür.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None, skills_root: str = ".agent/skills"):
        self.model_orch = model_orch or ModelOrchestrator()
        self.skills_root = skills_root

    async def synthesize_from_wisdom(self, db_session: Any) -> List[str]:
        """
        Memory'deki olgunlaşmış bilgeliği bulur ve beceri dosyaları üretir.
        """
        _log.info("Beceri Sentezi (Skill Synthesis) başlatılıyor...")
        
        # 1. Bilgelikleri çek (category='wisdom' and importance > 0.8)
        try:
            stmt = select(Memory).where(Memory.category == "wisdom").where(Memory.importance >= 0.8)
            result = await db_session.execute(stmt)
            wisdom_entries = result.scalars().all()
        except Exception:
            # DB hatası durumunda fallback (mock verileri)
            wisdom_entries = []
            _log.warning("Memory tablosu sorgulanamadı, otonom sentez atlanıyor.")
        
        created_skills = []
        for entry in wisdom_entries:
            skill_name = f"auto-{entry['topic'].replace('_', '-')}"
            skill_dir = os.path.join(self.skills_root, skill_name)
            
            if os.path.exists(os.path.join(skill_dir, "SKILL.md")):
                continue
            
            _log.info(f"Yeni Beceri Sentezleniyor: {skill_name}")
            
            skill_content = await self._generate_skill_md(entry['topic'], entry['wisdom'])
            if skill_content:
                os.makedirs(skill_dir, exist_ok=True)
                with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
                    f.write(skill_content)
                created_skills.append(skill_name)
        
        return created_skills

    async def _generate_skill_md(self, topic: str, wisdom: str) -> Optional[str]:
        """LLM kullanarak standart SKILL.md formatında içerik üretir."""
        prompt = f"""
        Konu: {topic}
        Öğrenilen Bilgelik (Wisdom): {wisdom}
        
        Lütfen bu bilgiyi standart bir Claude Code SKILL.md dosyasına dönüştür.
        Format:
        ---
        description: "Kısa açıklama"
        ---
        # {topic}
        [Yönerge ve kod örnekleri]
        """
        
        try:
            response = await self.model_orch.complete_task(
                agent_role="technical_writer",
                prompt=prompt,
                system_prompt="Sen bir AGI Beceri Sentezleyicisisin. Teknik olarak doğru ve yüksek kaliteli SKILL.md dosyaları yazarsın."
            )
            return response.content
        except Exception as e:
            _log.error(f"Skill generation error for {topic}: {e}")
            return None

# Singleton
skill_synthesizer = SkillSynthesizer()
