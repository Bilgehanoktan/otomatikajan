import os
import json
from typing import List, Dict, Any, Optional
from observability.logging import get_logger
from pathlib import Path

_log = get_logger("agi_self_patcher")

class SelfPatcher:
    """
    AGI'nin 'Öz-Onarım' ve 'Bilişsel Yetenek Enjeksiyonu' katmanı.
    Diagnostic node tarafından önerilen onarımları fiziksel olarak uygular.
    """
    
    def __init__(self):
        # Ajan dizinini belirle
        self.agents_dir = Path("e:/ai_company_faz12.1/agents")
        self.dynamic_prompts_path = self.agents_dir / "dynamic_prompts.json"
        self.dynamic_agents_path = self.agents_dir / "dynamic_agents.json"

    def patch_agent_prompt(self, agent_id: str, new_prompt: str) -> bool:
        """Belirli bir ajanın sistem promptunu dinamik olarak günceller."""
        _log.info(f"[SELF-PATCHER] Ajan promptu güncelleniyor: {agent_id}")
        
        try:
            prompts = {}
            if self.dynamic_prompts_path.exists():
                with open(self.dynamic_prompts_path, "r", encoding="utf-8") as f:
                    prompts = json.load(f)
            
            prompts[agent_id] = new_prompt
            
            with open(self.dynamic_prompts_path, "w", encoding="utf-8") as f:
                json.dump(prompts, f, indent=4, ensure_ascii=False)
            
            _log.info(f"[SELF-PATCHER] Ajan '{agent_id}' başarıyla yamalandı.")
            return True
        except Exception as e:
            _log.error(f"[SELF-PATCHER] Prompt yama hatası: {e}")
            return False

    def inject_specialist_agent(self, agent_data: Dict[str, Any]) -> bool:
        """Sisteme tamamen yeni bir dinamik uzman ajan enjekte eder."""
        _log.info(f"[SELF-PATCHER] Yeni uzman ajan enjekte ediliyor: {agent_data.get('id')}")
        
        try:
            agents = []
            if self.dynamic_agents_path.exists():
                with open(self.dynamic_agents_path, "r", encoding="utf-8") as f:
                    agents = json.load(f)
            
            # Eğer ajan zaten varsa güncelle, yoksa ekle
            existing_idx = next((i for i, a in enumerate(agents) if a["id"] == agent_data["id"]), -1)
            if existing_idx >= 0:
                agents[existing_idx] = agent_data
            else:
                agents.append(agent_data)
            
            with open(self.dynamic_agents_path, "w", encoding="utf-8") as f:
                json.dump(agents, f, indent=4, ensure_ascii=False)
            
            _log.info(f"[SELF-PATCHER] Uzman ajan '{agent_data['id']}' başarıyla enjekte edildi.")
            return True
        except Exception as e:
            _log.error(f"[SELF-PATCHER] Ajan enjeksiyon hatası: {e}")
            return False

# --- Singleton Export ---
self_patcher = SelfPatcher()
