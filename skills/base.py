from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillRequest:
    task_type: str
    title: str
    description: str
    project_id: str | None = None
    agent_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResult:
    success: bool
    skill_id: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class BaseSkillAdapter:
    skill_id: str = "base"

    def can_handle(self, req: SkillRequest) -> bool:
        return False

    async def execute(self, req: SkillRequest) -> SkillResult:
        raise NotImplementedError
