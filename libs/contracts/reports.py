from pydantic import BaseModel, Field
from typing import List
from libs.contracts.artifacts import Artifact
from libs.contracts.agents import AgentContribution

class FinalReport(BaseModel):
    """Müşteriye/Arayüze sunulacak sentezlenmiş sonuç"""
    task_id: str
    executive_summary: str
    consolidated_artifacts: List[Artifact] = Field(default_factory=list)
    contributions: List[AgentContribution]
    total_cost_usd: float
    total_latency_s: float
    unresolved_issues: List[str] = Field(default_factory=list)
    needs_human_action: bool = False
