from packages.skills.adapters.browser_research_adapter import BrowserResearchSkillAdapter
from packages.skills.adapters.browser_validator_adapter import BrowserValidatorSkillAdapter
from packages.skills.adapters.strategic_planning_adapter import StrategicPlanningSkillAdapter
from packages.skills.adapters.system_guard_adapter import SystemGuardSkillAdapter
from packages.skills.adapters.debugging_adapter import DebuggingSkillAdapter
from packages.skills.adapters.file_search_adapter import FileSearchSkillAdapter
from packages.skills.adapters.optimization_adapter import OptimizationSkillAdapter
from packages.skills.adapters.skill_creator_adapter import SkillCreatorSkillAdapter
from packages.skills.adapters.vault_memory_adapter import VaultMemorySkillAdapter


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
        from packages.skills.logger import log_skill_execution
        from packages.skills.base import SkillResult, SkillRequest
        
        adapter = self.get(skill_id)
        if not adapter:
            from packages.skills.base import SkillResult
            return SkillResult(success=False, skill_id=skill_id, summary=f"Beceri bulunamadı: {skill_id}")

        start_t = time.time()
        try:
            res = await adapter.execute(req)
            duration = time.time() - start_t
            await log_skill_execution(req, res, duration)
            return res
        except Exception as e:
            duration = time.time() - start_t
            from packages.skills.base import SkillResult
            res = SkillResult(success=False, skill_id=skill_id, summary=f"Hata: {str(e)}")
            await log_skill_execution(req, res, duration)
            return res


skill_registry = SkillRegistry()
