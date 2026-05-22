from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class SuggestionActionRequest(BaseModel):
    operator_id: str = Field(..., min_length=1, description="Operator ID cannot be empty.")
    rationale: str = Field(..., min_length=1, description="Rationale cannot be empty.")
    risk_acknowledgement: bool = Field(default=False, description="Must acknowledge risk if severity is CRITICAL or HIGH.")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SuggestionActionLog(BaseModel):
    action_id: str
    suggestion_id: str
    action: str
    from_status: str
    to_status: str
    operator_id: str
    rationale: str
    risk_acknowledgement: bool
    created_at: str
    result: Dict[str, Any] = Field(default_factory=dict)
