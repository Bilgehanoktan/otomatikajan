import logging
from typing import Dict, List, Optional
from services.orchestration.application.skill_catalog import skill_catalog
from services.orchestration.domain.models import ContextPackage

logger = logging.getLogger("core.prompt_manager")

class PromptManager:
    """
    Birleşik Prompt Assembly Katmanı (Faz 12.1).
    Ajanlar için dinamik, skill ve kural tabanlı sistem promptları oluşturur.
    """
    def __init__(self, rules_dir: str = "rules"):
        self.rules_dir = rules_dir
        self._patches: Dict[str, str] = {}
        self._governance_contract: str = ""
        self._load_governance_contract()

    def _load_governance_contract(self):
        """Temel kalite ve yönetim kontratını yükler."""
        contract_path = os.path.join(self.rules_dir, "common-coding-style.md")
        if os.path.exists(contract_path):
            try:
                with open(contract_path, "r", encoding="utf-8") as f:
                    self._governance_contract = f.read()
                logger.info("✅ Governance kontratı yüklendi.")
            except Exception as e:
                logger.error(f"❌ Governance kontratı yüklenemedi: {e}")
        else:
            self._governance_contract = "Maintain clean code, follow TDD, and ensure security."

    def set_agent_patch(self, agent_id: str, patch: str):
        """Ajan için yeni bir stratejik bağlam yaması ekler."""
        logger.debug(f"📝 PromptManager: {agent_id} için yama güncellendi.")
        self._patches[agent_id] = patch

    def get_agent_patch(self, agent_id: str) -> str:
        return self._patches.get(agent_id, "")

    def apply_patch(self, agent_id: str, base_prompt: str) -> str:
        """Geriye dönük uyumluluk için assembly katmanını çağırır."""
        return self.assemble_prompt(agent_id, base_prompt)

    def assemble_prompt(self, 
                       agent_id: str, 
                       base_prompt: str, 
                       context: Optional[ContextPackage] = None,
                       task_context: str = "") -> str:
        """
        Prompt Assembly Akışı (Sıralı):
        1. Temel ajan promptu
        2. Clean code / governance kontratı
        3. Seçili skill özetleri
        4. Dinamik patch
        5. Görev bağlamı
        """
        blocks = []

        # 1. Temel Ajan Promptu
        blocks.append(f"### 🤖 AJAN ROLÜ: {agent_id.upper()}\n{base_prompt}")

        # 2. Clean Code / Governance Kontratı
        if self._governance_contract:
            blocks.append(f"### 🛡️ GOVERNANCE & QUALITY CONTRACT\n{self._governance_contract}")

        # 3. Seçili Skill Özetleri
        if context and context.selected_skill_ids:
            skill_summaries = []
            for sid in context.selected_skill_ids:
                summary = skill_catalog.get_skill_summary(sid)
                if summary:
                    skill_summaries.append(summary)
            
            if skill_summaries:
                blocks.append("### 🛠️ ACTIVE SKILLS (ECC Core)\n" + "\n".join(skill_summaries))

        # 4. Dinamik Patch (Strategist verisi vb.)
        patch = self.get_agent_patch(agent_id)
        if patch:
            blocks.append(f"### ⚡ DYNAMIC CONTEXT PATCH\n{patch}")

        # 5. Görev Bağlamı
        if task_context:
            blocks.append(f"### 📋 TASK CONTEXT\n{task_context}")

        return "\n\n".join(blocks)

import os
# Singleton instance
prompt_manager = PromptManager()
