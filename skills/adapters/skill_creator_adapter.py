from pathlib import Path

from skills.base import BaseSkillAdapter, SkillRequest, SkillResult


class SkillCreatorSkillAdapter(BaseSkillAdapter):
    skill_id = "skill_creator"

    def __init__(self, generated_dir: str = "skills/generated"):
        self.generated_dir = Path(generated_dir)

    def can_handle(self, req: SkillRequest) -> bool:
        text = f"{req.title} {req.description}".lower()
        return any(k in text for k in ["skill", "workflow", "template", "repeat", "reusable", "beceri"])

    async def execute(self, req: SkillRequest) -> SkillResult:
        try:
            # Prioritize specific skill_id from context, fallback to title
            skill_id = req.context.get("skill_id") if req.context else None
            base_name = skill_id or req.title
            
            slug = base_name.lower().replace(" ", "_").replace("/", "_").replace("\\", "_")[:50] or "generated_skill"
            import re
            slug = re.sub(r"_+", "_", slug).strip("_")
            
            root = self.generated_dir / slug
            root.mkdir(parents=True, exist_ok=True)

            skill_md = root / "SKILL.md"
            manifest = root / "manifest.json"

            skill_md.write_text(
                f"""# {req.title}

## Purpose
{req.description}

## Inputs
- task
- context

## Outputs
- summary
- actions

## Rules
- deterministic ol
- mevcut sistem kontratlarını bozma
- önce analiz et sonra üret
- repair ve orchestrator ile uyumlu kal
""",
                encoding="utf-8",
            )

            manifest.write_text(
                f"""{{
  "id": "{slug}",
  "name": "{req.title}",
  "status": "draft",
  "owner": "skill_creator",
  "approval_required": true
}}""",
                encoding="utf-8",
            )

            return SkillResult(
                success=True,
                skill_id=self.skill_id,
                summary="Yeni skill taslağı üretildi",
                data={
                    "path": str(skill_md.absolute()),
                    "manifest": str(manifest.absolute()),
                },
            )
        except Exception as e:
            return SkillResult(
                success=False,
                skill_id=self.skill_id,
                summary=f"Skill üretimi başarısız: {e}",
            )
