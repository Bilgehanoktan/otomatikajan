import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from libs.db.models.ui_repair_models import UIIncidentWarRoom, IncidentSource, IncidentSeverity, WarRoomStatus
from datetime import datetime, timezone

class IncidentCorrelationEngine:
    def __init__(self, db: Session):
        self.db = db

    def correlate_finding(self, source_type: IncidentSource, source_id: uuid.UUID, 
                          tenant_key: Optional[str] = None, project_key: Optional[str] = None, 
                          cluster_key: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[UIIncidentWarRoom]:
        """
        Attempts to correlate a new finding with an existing open War Room.
        If a match is found, returns the existing War Room. Otherwise, returns None.
        """
        # 1. Search for open War Rooms with the same source pattern or same context
        # Check by tenant + project + cluster + source_type
        existing = self.db.query(UIIncidentWarRoom).filter(
            UIIncidentWarRoom.status.in_([WarRoomStatus.OPEN, WarRoomStatus.INVESTIGATING, WarRoomStatus.MITIGATING]),
            UIIncidentWarRoom.tenant_key == tenant_key,
            UIIncidentWarRoom.project_key == project_key,
            UIIncidentWarRoom.cluster_key == cluster_key,
            UIIncidentWarRoom.source_type == source_type
        ).first()

        if existing:
            return existing

        # 2. Heuristic: Check if there's a P0/P1 incident that might be related (same tenant/cluster)
        # Even if source_type is different, we might want to correlate if it's the same blast radius
        related = self.db.query(UIIncidentWarRoom).filter(
            UIIncidentWarRoom.status.in_([WarRoomStatus.OPEN, WarRoomStatus.INVESTIGATING, WarRoomStatus.MITIGATING]),
            UIIncidentWarRoom.tenant_key == tenant_key,
            UIIncidentWarRoom.cluster_key == cluster_key,
            UIIncidentWarRoom.severity.in_([IncidentSeverity.P0_CRITICAL, IncidentSeverity.P1_HIGH])
        ).first()

        if related:
            return related

        return None

    def group_incidents(self, war_room_ids: List[uuid.UUID], target_war_room_id: uuid.UUID):
        """
        Groups multiple war rooms into a single target war room (manual or suggested merging).
        """
        # In a real implementation, this would update child incidents to point to a parent
        # or merge their timelines. For now, we'll keep it simple.
        pass
