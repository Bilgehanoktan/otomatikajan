import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from libs.db.models.ui_repair_models import UIIncidentTimelineEvent, UIIncidentWarRoom
from datetime import datetime, timezone

class IncidentTimelineBuilder:
    def __init__(self, db: Session):
        self.db = db

    def add_event(self, war_room_id: uuid.UUID, event_type: str, actor: str, message: str, 
                  source_ref: Optional[str] = None, payload: Optional[Dict[str, Any]] = None, 
                  evidence_hash: Optional[str] = None) -> UIIncidentTimelineEvent:
        """
        Adds a new event to the incident timeline.
        """
        event = UIIncidentTimelineEvent(
            war_room_id=war_room_id,
            event_type=event_type,
            actor=actor,
            message=message,
            source_ref=source_ref,
            payload_json=payload or {},
            evidence_hash=evidence_hash
        )
        self.db.add(event)
        self.db.flush()
        return event

    def get_timeline(self, war_room_id: uuid.UUID) -> List[UIIncidentTimelineEvent]:
        return self.db.query(UIIncidentTimelineEvent).filter(
            UIIncidentTimelineEvent.war_room_id == war_room_id
        ).order_by(UIIncidentTimelineEvent.created_at.asc()).all()
