import os
import json
import logging
from typing import Dict, Any, Optional
from observability.logging import get_logger
from llm.model_orchestrator import ModelOrchestrator

_log = get_logger("core.agency.factory")

class SpecialistFactory:
    def __init__(self, model_orch: ModelOrchestrator, library_path: str):
        self.model_orch = model_orch
        self.library_path = library_path
        self.dynamic_path = os.path.join(library_path, "dynamic")
        os.makedirs(self.dynamic_path, exist_ok=True)

    async def build_specialist(self, agent_id: str, context_prompt: str) -> Optional[Dict[str, Any]]:
        """
        Gorev baglamina gore yeni bir uzman ajan (Specialist) uretir.
        """
        _log.info(f"[FACTORY] Yeni uzman ajan uretiliyor: {agent_id}")
        
        system_gen_prompt = f"""
Sen bir 'Agent Architect'sin. Sistemde '{agent_id}' kimligine sahip bir uzmana ihtiyac duyuldu.
Bu uzman, su gorevi/baglami cozmek icin ozellesmeli:
---
{context_prompt}
---

Lutfen bu ajan icin asagidaki JSON formatinda bir tanim uret:
{{
  "name": "Ajana verilecek isim (orn: Kubernetes Guvenlik Uzmani)",
  "role": "Ajana verilecek rol (orn: SRE / Security)",
  "emoji": "Ajani temsil eden bir emoji",
  "system_prompt": "Ajana verilecek kapsamli, yetenekli ve disiplinli sistem istemi. Faz 12 standartlarina uygun olmali.",
  "category": "Ajanin dahil olacagi kategori (orn: devops, security, data)"
}}

Sadece gecerli bir JSON dunu. Aciklama ekleme.
"""
        try:
            response = await self.model_orch.generate(system_gen_prompt)
            # JSON temizle (markdown block vs varsa)
            clean_json = response.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                 clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
            data = json.loads(clean_json)
            
            # MD dosyasi olarak kaydet (Self-healing & Persistence)
            file_content = f"""---
name: {data.get('name', agent_id)}
role: {data.get('role', 'Specialist')}
emoji: {data.get('emoji', '🤖')}
category: {data.get('category', 'dynamic')}
source: dynamic_factory
---
{data.get('system_prompt', '')}
"""
            file_name = f"{agent_id}.md"
            full_path = os.path.join(self.dynamic_path, file_name)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(file_content)
                
            _log.info(f"[OK] Yeni uzman kaydedildi: {full_path}")
            
            # Ajan verisini don
            return {
                "id": agent_id,
                "name": data.get("name"),
                "role": data.get("role"),
                "system_prompt": data.get("system_prompt"),
                "emoji": data.get("emoji", "🤖"),
                "category": data.get("category", "dynamic")
            }

        except Exception as e:
            _log.error(f"[ERROR] SpecialistFactory fail: {e}")
            return None

# Singleton or helper function
def get_specialist_factory(model_orch: ModelOrchestrator) -> SpecialistFactory:
    from packages.orchestration.agency.loader import agency_loader
    return SpecialistFactory(model_orch, agency_loader.base_dir)
