from datetime import datetime, timezone
from pathlib import Path

from skills.base import BaseSkillAdapter, SkillRequest, SkillResult


class VaultMemorySkillAdapter(BaseSkillAdapter):
    skill_id = "vault_memory"

    def __init__(self, vault_root: str = "memory/vault"):
        self.vault_root = Path(vault_root)
        self.vault_root.mkdir(parents=True, exist_ok=True)

    def can_handle(self, req: SkillRequest) -> bool:
        return True

    def _slugify(self, text: str) -> str:
        slug = text.lower().strip().replace(" ", "-").replace("/", "-").replace("\\", "-")
        # remove special chars
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        # Remove multiple dashes and trailing/leading
        import re
        slug = re.sub(r"-+", "-", slug).strip("-")
        return slug[:80] or "untitled"

    async def execute(self, req: SkillRequest) -> SkillResult:
        try:
            slug = self._slugify(req.title)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            note_path = self.vault_root / f"{timestamp}_{slug}.md"

            content = f"""---
type: task_memory
created_at: {datetime.now(timezone.utc).isoformat()}
project_id: {req.project_id or ""}
agent_id: {req.agent_id or ""}
task_type: {req.task_type}
---

# {req.title}

## Description
{req.description}

## Context Snippet
{str(req.context)[:2000]}

## Links
- [[incidents]]
- [[patterns]]
- [[architectural-decisions]]
"""

            note_path.write_text(content, encoding="utf-8")

            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                summary=f"Vault note yazıldı: {note_path.name}",
                data={"path": str(note_path.absolute())},
            )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                summary=f"Vault yazımı başarısız: {e}",
            )
