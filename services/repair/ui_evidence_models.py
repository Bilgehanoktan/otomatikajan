from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UIConsoleLog(BaseModel):
    level: str
    message: str
    timestamp: datetime
    source: Optional[str] = None

class UIEvidencePack(BaseModel):
    case_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    video_path: Optional[str] = None
    console_logs: List[UIConsoleLog] = Field(default_factory=list)
    page_url: str
    page_title: str
    viewport_size: Dict[str, int]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UIEvidenceRequest(BaseModel):
    case_id: str
    target_url: str
    capture_screenshot: bool = True
    capture_trace: bool = True
    capture_console: bool = True
    timeout_ms: int = 30000
