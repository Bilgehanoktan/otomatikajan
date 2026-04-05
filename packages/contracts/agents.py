from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from packages.contracts.states import AgentStatus
from packages.contracts.artifacts import Artifact
from packages.contracts.errors import ErrorDetail

class AgentContribution(BaseModel):
    agent_id: str
    status: str
    summary: str
    cost_contribution: float
    
class SubtaskOutput(BaseModel):
    """Ajanların dönmek zorunda olduğu standart format"""
    task_id: str
    subtask_id: str
    agent_id: str
    
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0
    
    status: AgentStatus
    summary: str
    raw_output: str
    artifacts: List[Artifact] = Field(default_factory=list)
    error: Optional[ErrorDetail] = None
    
    started_at: datetime
    completed_at: datetime
