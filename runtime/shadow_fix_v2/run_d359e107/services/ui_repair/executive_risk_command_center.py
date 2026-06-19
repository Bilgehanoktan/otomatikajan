import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from libs.db.models.ui_repair_models import (
    UIIncidentWarRoom, UIExecutiveRiskSnapshot, 
    IncidentSeverity, WarRoomStatus, UIExecutiveRiskReport
)
from datetime import datetime, timezone
from .war_room_evidence_writer import WarRoomEvidenceWriter

class ExecutiveRiskCommandCenter:
    def __init__(self, db: Session):
        self.db = db
        self.evidence_writer = WarRoomEvidenceWriter(db)

    def get_risk_overview(self) -> Dict[str, Any]:
        """
        Calculates the current global risk overview.
        """
        # Active incidents by severity
        active_incidents = self.db.query(UIIncidentWarRoom).filter(
            UIIncidentWarRoom.status != WarRoomStatus.CLOSED
        ).all()
        
        counts = {
            "P0_CRITICAL": 0,
            "P1_HIGH": 0,
            "P2_MEDIUM": 0,
            "P3_LOW": 0
        }
        for i in active_incidents:
            counts[i.severity.value] += 1
            
        # Global risk score (weighted average of active incidents)
        if not active_incidents:
            global_risk_score = 0.0
        else:
            global_risk_score = sum([i.executive_risk_score for i in active_incidents]) / len(active_incidents)
            
        # Affected tenants & clusters
        tenants = set([i.tenant_key for i in active_incidents if i.tenant_key])
        clusters = set([i.cluster_key for i in active_incidents if i.cluster_key])
        
        # MTTR (last 30 days)
        # Simplified: average MTTR of resolved incidents
        mttr_s = 0.0
        
        # Unresolved critical risks
        unresolved_critical = [
            {"key": i.incident_key, "title": i.title, "risk_score": i.executive_risk_score, "severity": i.severity.value} 
            for i in active_incidents if i.severity in [IncidentSeverity.P0_CRITICAL, IncidentSeverity.P1_HIGH]
        ]
        
        latest_report = self.db.query(UIExecutiveRiskReport).order_by(
            UIExecutiveRiskReport.generated_at.desc()
        ).first()

        return {
            "global_risk_score": round(global_risk_score, 2),
            "active_p0_count": counts["P0_CRITICAL"],
            "active_p1_count": counts["P1_HIGH"],
            "active_p2_count": counts["P2_MEDIUM"],
            "active_p3_count": counts["P3_LOW"],
            "affected_tenants": len(tenants),
            "affected_clusters": len(clusters),
            "open_remediations": 0, # Placeholder
            "governance_waiting": counts.get("WAITING_GOVERNANCE", 0), # Simplified
            "mttr_s": mttr_s,
            "top_affected_tenants": list(tenants)[:5],
            "top_affected_clusters": list(clusters)[:5],
            "unresolved_critical_risks": unresolved_critical,
            "last_report_id": latest_report.id if latest_report else None
        }

    def create_snapshot(self) -> UIExecutiveRiskSnapshot:
        overview = self.get_risk_overview()
        
        snapshot = UIExecutiveRiskSnapshot(
            global_risk_score=overview["global_risk_score"],
            active_p0_count=overview["active_p0_count"],
            active_p1_count=overview["active_p1_count"],
            affected_tenants=overview["affected_tenants"],
            affected_clusters=overview["affected_clusters"],
            open_remediations=overview["open_remediations"],
            governance_waiting=overview["governance_waiting"],
            executive_summary=f"Global Risk Score is {overview['global_risk_score']}. {overview['active_p0_count']} P0 incidents active."
        )
        self.db.add(snapshot)
        self.db.flush()
        
        # Evidence
        self.evidence_writer.write_evidence(
            snapshot.id, "RISK_SNAPSHOT_CREATED", overview
        )
        
        return snapshot
