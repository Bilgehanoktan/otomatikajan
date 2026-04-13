import logging
from typing import Dict, Any
from core.prompt_manager import prompt_manager

logger = logging.getLogger("tools.strategy_tools")

class StrategyTools:
    """
    Strategist ajanının sistem üzerinde stratejik müdahaleler 
    yapmasını sağlayan araç seti.
    """
    @staticmethod
    async def patch_agent_prompt(agent_id: str, strategic_context: str) -> str:
        """
        Belirtilen ajanın sistem promptuna stratejik bağlam ekler.
        Örn: 'backend_dev' ajanına '2026 async best practices' bağlamı eklemek.
        """
        try:
            prompt_manager.set_agent_patch(agent_id, strategic_context)
            logger.info(f"🎯 Stratejik yama uygulandı: {agent_id}")
            return f"{agent_id} için stratejik bağlam başarıyla güncellendi."
        except Exception as e:
            logger.error(f"Patch hatası: {e}")
            return f"Hata oluştu: {str(e)}"

    @staticmethod
    def get_current_patches() -> Dict[str, str]:
        """Tüm aktif stratejik yamaları listeler."""
        return prompt_manager._patches

def get_strategy_tools() -> StrategyTools:
    return StrategyTools()
