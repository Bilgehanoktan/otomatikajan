from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UIElementInfo(BaseModel):
    selector: str
    role: str
    text: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    is_visible: bool = True

class UIDiagnosisResult(BaseModel):
    case_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    root_cause_summary: str
    suspected_elements: List[UIElementInfo] = Field(default_factory=list)
    suggested_fix_strategy: str
    confidence_score: float
    analysis_details: str
    technical_brief: Dict[str, Any] = Field(default_factory=dict)

class UIDiagnosisRequest(BaseModel):
    case_id: str
    evidence_pack_path: str
    symptom_description: str
    use_stagehand: bool = True
