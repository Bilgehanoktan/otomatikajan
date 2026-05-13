from __future__ import annotations

from dataclasses import dataclass

from services.repair.agent_backends.base import AgentResult
from services.repair.repair_models import RepairCase


@dataclass
class DeferredBackendConfig:
    name: str
    source_repo: str
    reason: str


class DeferredAgentBackend:
    def __init__(self, config: DeferredBackendConfig):
        self.config = config
        self.name = config.name

    def generate_patch(
        self,
        repair_case: RepairCase,
        *,
        work_dir: str = "",
        timeout_seconds: int = 120,
    ) -> AgentResult:
        return AgentResult(
            diff_text="",
            changed_files=[],
            agent_summary=(
                f"{self.config.source_repo} adapter kayitli, ancak guvenli ilk fazda "
                "dogrudan agent calistirma devre disi."
            ),
            confidence=0.0,
            exit_status="deferred",
            error=self.config.reason,
            trajectory=[
                {
                    "source_repo": self.config.source_repo,
                    "backend": self.config.name,
                    "status": "safe_deferred",
                    "incident_id": repair_case.incident_id,
                }
            ],
        )


def make_deferred_backend(name: str, source_repo: str, reason: str) -> type[DeferredAgentBackend]:
    class NamedDeferredBackend(DeferredAgentBackend):
        def __init__(self, *args, **kwargs):
            super().__init__(DeferredBackendConfig(name=name, source_repo=source_repo, reason=reason))

    NamedDeferredBackend.__name__ = "".join(part.capitalize() for part in name.split("_")) + "DeferredBackend"
    return NamedDeferredBackend

