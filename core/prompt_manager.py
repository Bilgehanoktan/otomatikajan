import logging
from typing import Dict, Optional

logger = logging.getLogger("core.prompt_manager")

class PromptManager:
    """
    Dinamik Prompt Yönetim Sistemi.
    Strategist ajanı tarafından üretilen güncel pazar bilgilerini 
    diğer ajanların sistem promptlarına enjekte eder.
    """
    def __init__(self):
        # agent_id -> prompt_patch
        self._patches: Dict[str, str] = {}

    def set_agent_patch(self, agent_id: str, patch: str):
        """Ajan için yeni bir stratejik bağlam yaması ekler."""
        logger.info(f"📝 PromptManager: {agent_id} için yeni yama kaydedildi.")
        self._patches[agent_id] = patch

    def get_agent_patch(self, agent_id: str) -> str:
        """Ajan için kayıtlı yamayı döner, yoksa boş string döner."""
        return self._patches.get(agent_id, "")

    def apply_patch(self, agent_id: str, base_prompt: str) -> str:
        """Base prompt'a stratejik yamayı ekler."""
        patch = self.get_agent_patch(agent_id)
        if not patch:
            return base_prompt
            
        return f"{base_prompt}\n\n### 🛡️ GÜNCEL STRATEJİK BAĞLAM (Dinamik):\n{patch}"

# Singleton instance
prompt_manager = PromptManager()
