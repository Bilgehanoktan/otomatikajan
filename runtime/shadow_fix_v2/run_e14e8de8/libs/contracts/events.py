"""
Event Contracts — Sistem genelindeki olay tipleri ve veri yapıları.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

@dataclass
class WebSocketEvent:
    event: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: dict = field(default_factory=dict)

# Olay Tipleri (Constants)
EVENT_JOB_PROGRESS = "job_progress"
EVENT_LIVE_PATCH   = "live_patch"
EVENT_DEBATE_STATE = "debate_state"
EVENT_SKILL_TRACE  = "skill_trace"
EVENT_SYSTEM_PULSE = "system_pulse"
