from pathlib import Path

from skills.base import BaseSkillAdapter, SkillRequest, SkillResult


class FileSearchSkillAdapter(BaseSkillAdapter):
    skill_id = "file_search"

    def can_handle(self, req: SkillRequest) -> bool:
        return True

    async def execute(self, req: SkillRequest) -> SkillResult:
        try:
            from packages.orchestration.indexing.system_indexer import SystemIndexer

            project_root = Path(".")
            indexer = SystemIndexer(project_root=str(project_root.absolute()))

            query = f"{req.title} {req.description}".strip()
            hits = indexer.search(query=query, limit=8)
            
            # Impact analysis might not exist yet, we'll implement it next
            impact = []
            if hasattr(indexer, "impact_analysis"):
                impact = indexer.impact_analysis(query=query, limit=6)

            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                summary=f"{len(hits)} aday dosya bulundu, {len(impact)} etki adayı çıkarıldı",
                data={
                    "hits": hits,
                    "impact_candidates": impact,
                },
            )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                summary=f"Dosya araması başarısız: {e}",
            )
