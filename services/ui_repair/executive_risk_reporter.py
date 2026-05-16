import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from libs.db.models.ui_repair_models import (
    UIIncidentWarRoom, UIExecutiveRiskReport, 
    IncidentSeverity, WarRoomStatus
)
from datetime import datetime, timezone, timedelta
from .war_room_evidence_writer import WarRoomEvidenceWriter

class ExecutiveRiskReporter:
    def __init__(self, db: Session):
        self.db = db
        self.evidence_writer = WarRoomEvidenceWriter(db)

    def generate_report(self, report_name: str, period_days: int = 7) -> UIExecutiveRiskReport:
        """
        Generates an executive risk report for the specified period.
        """
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=period_days)
        
        # Query incidents in period
        incidents = self.db.query(UIIncidentWarRoom).filter(
            UIIncidentWarRoom.created_at >= period_start
        ).all()
        
        total_incidents = len(incidents)
        p0_count = len([i for i in incidents if i.severity == IncidentSeverity.P0_CRITICAL])
        p1_count = len([i for i in incidents if i.severity == IncidentSeverity.P1_HIGH])
        
        # Calculate MTTR
        resolved_incidents = [i for i in incidents if i.resolved_at and i.opened_at]
        mttr_s = 0.0
        if resolved_incidents:
            total_time = sum([(i.resolved_at - i.opened_at).total_seconds() for i in resolved_incidents])
            mttr_s = total_time / len(resolved_incidents)
            
        # Top risk domains
        unresolved = [i for i in incidents if i.status != WarRoomStatus.CLOSED]
        unresolved_risks = [
            {"key": i.incident_key, "title": i.title, "risk_score": i.executive_risk_score} 
            for i in unresolved[:10]
        ]
        
        # Recommend actions
        recommendation = "Maintain current posture."
        if p0_count > 0:
            recommendation = "Urgent review of P0 incidents and root causes required."
        elif mttr_s > 86400: # > 24 hours
            recommendation = "Improve incident response velocity for critical paths."

        report = UIExecutiveRiskReport(
            report_name=report_name,
            period_start=period_start,
            period_end=period_end,
            total_incidents=total_incidents,
            p0_count=p0_count,
            p1_count=p1_count,
            mttr_s=mttr_s,
            unresolved_risks_json=unresolved_risks,
            top_risk_domains_json=list(set([i.source_type.value for i in incidents])),
            recommendation=recommendation,
            report_path=f"/reports/risk/{report_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:4]}.pdf",
            generated_at=datetime.now(timezone.utc)
        )
        self.db.add(report)
        self.db.flush()
        
        # Evidence
        evidence_hash = self.evidence_writer.write_evidence(
            report.id, "EXECUTIVE_REPORT_GENERATED", 
            {"report_name": report_name, "total_incidents": total_incidents, "p0_count": p0_count}
        )
        report.evidence_hash = evidence_hash
        
        return report
