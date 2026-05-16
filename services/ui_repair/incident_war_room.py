import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from libs.db.models.ui_repair_models import (
    UIIncidentWarRoom, UIIncidentActionItem, 
    IncidentSource, IncidentSeverity, WarRoomStatus
)
from .incident_correlation_engine import IncidentCorrelationEngine
from .blast_radius_analyzer import BlastRadiusAnalyzer
from .business_impact_scorer import BusinessImpactScorer
from .incident_commander_recommender import IncidentCommanderRecommender
from .incident_timeline_builder import IncidentTimelineBuilder
from .war_room_evidence_writer import WarRoomEvidenceWriter
from datetime import datetime, timezone

class IncidentWarRoomManager:
    def __init__(self, db: Session):
        self.db = db
        self.correlation_engine = IncidentCorrelationEngine(db)
        self.blast_analyzer = BlastRadiusAnalyzer(db)
        self.impact_scorer = BusinessImpactScorer()
        self.commander_recommender = IncidentCommanderRecommender(db)
        self.timeline_builder = IncidentTimelineBuilder(db)
        self.evidence_writer = WarRoomEvidenceWriter(db)

    def create_or_update_incident(self, source_type: IncidentSource, source_id: uuid.UUID, 
                                  title: Optional[str] = None, tenant_key: Optional[str] = None, 
                                  project_key: Optional[str] = None, cluster_key: Optional[str] = None, 
                                  metadata: Optional[Dict[str, Any]] = None) -> UIIncidentWarRoom:
        """
        Coordinates the creation or correlation of an incident.
        """
        # 1. Correlate
        existing = self.correlation_engine.correlate_finding(
            source_type, source_id, tenant_key, project_key, cluster_key, metadata
        )
        
        if existing:
            # Add to timeline of existing
            self.timeline_builder.add_event(
                existing.id, "FINDING_CORRELATED", "WarRoom_Orchestrator", 
                f"New {source_type.value} finding ({source_id}) correlated to this incident.",
                source_ref=str(source_id)
            )
            return existing

        # 2. Analyze Blast Radius
        blast_radius = self.blast_analyzer.analyze(
            source_type, source_id, tenant_key, project_key, cluster_key, metadata
        )
        
        # 3. Calculate Scores
        scores = self.impact_scorer.calculate_scores(source_type, blast_radius, metadata)
        severity = self.impact_scorer.determine_severity(scores)
        
        # 4. Recommend Commander
        recommendation = self.commander_recommender.recommend(source_type, tenant_key, project_key)
        
        # 5. Create War Room
        incident_key = f"INC-{uuid.uuid4().hex[:8].upper()}"
        war_room = UIIncidentWarRoom(
            incident_key=incident_key,
            title=title or f"Incident: {source_type.value} in {tenant_key or 'Global'}",
            severity=severity,
            status=WarRoomStatus.OPEN,
            source_type=source_type,
            source_id=source_id,
            tenant_key=tenant_key,
            project_key=project_key,
            cluster_key=cluster_key,
            assigned_commander=recommendation["recommended_commander"],
            owner_team=recommendation["recommended_team"],
            blast_radius_json=blast_radius,
            business_impact_score=scores["business_impact_score"],
            executive_risk_score=scores["executive_risk_score"],
            opened_at=datetime.now(timezone.utc)
        )
        self.db.add(war_room)
        self.db.flush()
        
        # 6. Initial Evidence & Timeline
        evidence_hash = self.evidence_writer.write_evidence(
            war_room.id, "WAR_ROOM_CREATED", 
            {"incident_key": incident_key, "scores": scores, "blast_radius": blast_radius}
        )
        war_room.evidence_hash = evidence_hash
        
        self.timeline_builder.add_event(
            war_room.id, "INCIDENT_OPENED", "WarRoom_Orchestrator", 
            f"War Room opened for {source_type.value}. Initial risk score: {scores['executive_risk_score']}",
            evidence_hash=evidence_hash
        )
        
        self.timeline_builder.add_event(
            war_room.id, "COMMANDER_RECOMMENDED", "WarRoom_Orchestrator", 
            f"Recommended Commander: {war_room.assigned_commander} ({recommendation['recommended_team']}). Rationale: {recommendation['rationale']}"
        )

        return war_room

    def add_action_item(self, war_room_id: uuid.UUID, action_type: str, title: str, 
                        owner: str, due_at: Optional[datetime] = None) -> UIIncidentActionItem:
        action = UIIncidentActionItem(
            war_room_id=war_room_id,
            action_type=action_type,
            title=title,
            owner=owner,
            due_at=due_at
        )
        self.db.add(action)
        self.db.flush()
        
        self.timeline_builder.add_event(
            war_room_id, "ACTION_ITEM_CREATED", "WarRoom_Orchestrator", 
            f"Action Item created: {title}. Owner: {owner}"
        )
        return action

    def resolve_incident(self, war_room_id: uuid.UUID, rationale: str, actor: str) -> UIIncidentWarRoom:
        war_room = self.db.query(UIIncidentWarRoom).get(war_room_id)
        if not war_room:
            raise ValueError("War Room not found")
            
        war_room.status = WarRoomStatus.RESOLVED
        war_room.resolved_at = datetime.now(timezone.utc)
        
        evidence_hash = self.evidence_writer.write_evidence(
            war_room.id, "INCIDENT_RESOLVED", {"rationale": rationale, "actor": actor}
        )
        
        self.timeline_builder.add_event(
            war_room_id, "INCIDENT_RESOLVED", actor, 
            f"Incident resolved. Rationale: {rationale}",
            evidence_hash=evidence_hash
        )
        
        return war_room
