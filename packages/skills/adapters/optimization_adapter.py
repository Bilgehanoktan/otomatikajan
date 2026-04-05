from skills.base import BaseSkillAdapter, SkillRequest, SkillResult


class OptimizationSkillAdapter(BaseSkillAdapter):
    skill_id = "optimization"

    def can_handle(self, req: SkillRequest) -> bool:
        return True

    async def execute(self, req: SkillRequest) -> SkillResult:
        description = req.description or ""
        context = req.context or {}

        memories = context.get("memories", [])
        file_hits = context.get("file_hits", [])
        shared_context = context.get("shared_context", "")

        compact_memories = memories[:5]
        compact_files = file_hits[:5]
        
        # Safe string handling
        compact_shared = ""
        if isinstance(shared_context, str):
            compact_shared = shared_context[:4000]

        optimized = {
            "title": req.title[:200],
            "description": description[:2000],
            "memories": compact_memories,
            "file_hits": compact_files,
            "shared_context": compact_shared,
        }

        warnings: list[str] = []
        if len(description) > 2000:
            warnings.append("description trimmed to 2000 chars")
        if isinstance(shared_context, str) and len(shared_context) > 4000:
            warnings.append("shared_context trimmed to 4000 chars")

        return SkillResult(
            success=True,
            skill_id=self.skill_id,
            summary="Context optimize edildi",
            data=optimized,
            warnings=warnings,
        )
