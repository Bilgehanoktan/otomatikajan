"""
Sovereign Improvement Proposal Engine
───────────────────────────────────
Analyzes system telemetry, failures, and bottlenecks to cluster 
them into structured improvement proposals.
"""

from typing import List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.future import select
from libs.db.models.core_models import OperationalIncident, DomainEventLog, CEOSuggestedTask, ImprovementOpportunity
import logging

logger = logging.getLogger(__name__)

class ProposalEngine:
    def __init__(self, db_session):
        self.db = db_session

    async def analyze_failures(self) -> List[Dict[str, Any]]:
        """
        Scans OperationalIncidents and clusters them by type/pattern.
        Returns a list of potential improvements.
        """
        # 1. Fetch recent incidents
        result = await self.db.execute(
            select(OperationalIncident).where(OperationalIncident.status == "open")
        )
        incidents = result.scalars().all()
        
        if not incidents:
            return []

        # 2. Simple clustering logic (can be expanded with LLM)
        clusters = {}
        for inc in incidents:
            key = f"{inc.incident_type}:{inc.message[:50]}"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(inc)

        proposals = []
        for key, group in clusters.items():
            if len(group) >= 3: # Threshold for clustering
                proposals.append({
                    "title": f"Autonomic fix for repetitive issue: {group[0].incident_type}",
                    "description": f"Detected {len(group)} similar incidents. Pattern: {group[0].message}",
                    "severity": "medium",
                    "incidents": [str(i.id) for i in group]
                })

        return proposals

    async def create_improvement_opportunity(self, proposal: Dict[str, Any]) -> UUID:
        """Persists a clustered proposal as an ImprovementOpportunity."""
        opp = ImprovementOpportunity(
            id=uuid4(),
            source_type="anomaly_cluster",
            title=proposal["title"],
            description=proposal["description"],
            severity=proposal["severity"],
            status="open",
            evidence_detail=f"Linked Incidents: {', '.join(proposal['incidents'])}"
        )
        self.db.add(opp)
        await self.db.commit()
        return opp.id
