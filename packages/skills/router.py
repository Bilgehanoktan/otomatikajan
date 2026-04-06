from packages.skills.base import SkillRequest
from packages.skills.registry import skill_registry


class SkillRouter:
    def suggest(self, req: SkillRequest) -> list[str]:
        text = f"{req.title}\n{req.description}".lower()

        suggestions: list[str] = []

        if any(k in text for k in ["bug", "error", "incident", "fix", "recovery", "traceback", "failure", "hata"]):
            suggestions.extend(["debugging", "file_search", "vault_memory"])

        if any(k in text for k in ["repo", "codebase", "search", "dependency", "impact", "module", "index", "ara"]):
            suggestions.extend(["file_search", "optimization"])

        if any(k in text for k in ["context", "token", "optimize", "prompt", "memory", "hafıza"]):
            suggestions.extend(["optimization", "vault_memory"])

        if any(k in text for k in ["repeat", "reusable", "template", "new workflow", "new skill", "beceri", "şablon"]):
            suggestions.append("skill_creator")

        # Deduplicate
        deduped: list[str] = []
        for s in suggestions:
            if s not in deduped:
                deduped.append(s)
        return deduped

    async def run_suggested(self, req: SkillRequest):
        results = []
        suggested_ids = self.suggest(req)
        for skill_id in suggested_ids:
            skill = skill_registry.get(skill_id)
            if skill and skill.can_handle(req):
                results.append(await skill.execute(req))
        return results


skill_router = SkillRouter()
