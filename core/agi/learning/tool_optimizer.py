from typing import Optional, Any
from core.agi.schemas import EpisodeRecord
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

_log = get_logger("agi_tool_optimizer")

class ToolOptimizer:
    """
    Learning Core (Katman 7): Autonomous Tool Refinement.
    Otonom üretilen araçların kullanım istatistiklerini izler ve onları iyileştirir.
    """
    def __init__(self, model_orch: Optional[ModelOrchestrator] = None):
        self.model_orch = model_orch or ModelOrchestrator()

    async def optimize_dynamic_tools(self, episode: EpisodeRecord, db: Any):
        """
        Tamamlanan bölümdeki otonom araç kullanımlarını analiz eder ve gerekirse kod iyileştirmesi yapar.
        """
        for action in episode.actions:
            if action.success and action.tool_used.startswith("auto_tool_"):
                await self._harden_tool(action.tool_used)

    async def _harden_tool(self, tool_name: str):
        """
        Aracı "hardened" (dayanıklı) hale getirir.
        Gereksiz logları siler, error handling ekler, performansı artırır.
        """
        from core.agi.operational.tool_weaver import tool_registry
        tool_meta = tool_registry.get_tool(tool_name)
        if not tool_meta:
            return

        _log.info(f"Araç İyileştiriliyor (Hardening): {tool_name}")
        
        path = tool_meta["path"]
        with open(path, "r", encoding="utf-8") as f:
            old_code = f.read()

        prompt = f"""
        Aşağıdaki otonom üretilmiş Python kodunu 'üretim kalitesine' yükselt:
        
        {old_code}
        
        İyileştirmeler:
        1. Tip belirteçleri (type hints) ekle.
        2. Docstring ekle.
        3. Exception handling'i derinleştir.
        4. Varsa performans darboğazlarını gider.
        
        SADECE kodu döndür.
        """

        try:
            response = await self.model_orch.complete_task(
                agent_role="senior_developer",
                prompt=prompt,
                system_prompt="Sen bir AGI Kod Optimizasyon Uzmanısın."
            )
            
            new_code = response.content.replace("```python", "").replace("```", "").strip()
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_code)
                
            _log.info(f"ARAÇ İYİLEŞTİRİLDİ: {tool_name}")
            
        except Exception as e:
            _log.error(f"Tool hardening hatası ({tool_name}): {e}")

# Singleton
tool_optimizer = ToolOptimizer()
