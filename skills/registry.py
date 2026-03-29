from skills.adapters.browser_research_adapter import BrowserResearchSkillAdapter
from skills.adapters.browser_validator_adapter import BrowserValidatorSkillAdapter
from skills.adapters.strategic_planning_adapter import StrategicPlanningSkillAdapter
from skills.adapters.system_guard_adapter import SystemGuardSkillAdapter
from skills.adapters.debugging_adapter import DebuggingSkillAdapter
from skills.adapters.file_search_adapter import FileSearchSkillAdapter
from skills.adapters.optimization_adapter import OptimizationSkillAdapter
from skills.adapters.skill_creator_adapter import SkillCreatorSkillAdapter
from skills.adapters.vault_memory_adapter import VaultMemorySkillAdapter


class SkillRegistry:
    def __init__(self):
        self._skills = {
            "optimization": OptimizationSkillAdapter(),
            "debugging": DebuggingSkillAdapter(),
            "file_search": FileSearchSkillAdapter(),
            "vault_memory": VaultMemorySkillAdapter(),
            "skill_creator": SkillCreatorSkillAdapter(),
            "browser_validator": BrowserValidatorSkillAdapter(),
            "strategic_planning": StrategicPlanningSkillAdapter(),
            "system_guard": SystemGuardSkillAdapter(),
            "browser_research": BrowserResearchSkillAdapter(),
        }

    def get(self, skill_id: str):
        return self._skills.get(skill_id)

    def all(self):
        return list(self._skills.values())

    def ids(self):
        return list(self._skills.keys())

    async def execute(self, skill_id: str, req: "SkillRequest") -> "SkillResult":
        """
        Beceri yürütür ve sonucunu otomatik olarak loglar.
        """
        import time
        from skills.logger import log_skill_execution
        from skills.base import SkillResult, SkillRequest
        
        adapter = self.get(skill_id)
        if not adapter:
            from skills.base import SkillResult
            return SkillResult(success=False, skill_id=skill_id, summary=f"Beceri bulunamadı: {skill_id}")

        start_t = time.time()
        try:
            res = await adapter.execute(req)
            duration = time.time() - start_t
            await log_skill_execution(req, res, duration)
            return res
        except Exception as e:
            duration = time.time() - start_t
            from skills.base import SkillResult
            res = SkillResult(success=False, skill_id=skill_id, summary=f"Hata: {str(e)}")
            await log_skill_execution(req, res, duration)
            return res


skill_registry = SkillRegistry()
