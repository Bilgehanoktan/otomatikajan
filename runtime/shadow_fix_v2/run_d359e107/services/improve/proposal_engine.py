from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
import logging
from sqlalchemy import select
from libs.db.models.core_models import OperationalIncident, Project, DomainEventLog, CEOSuggestedTask, ImprovementOpportunity, SystemImprovement
from services.improve.diagnosis_engine import DiagnosisEngine
from libs.llm.model_orchestrator import ModelOrchestrator

logger = logging.getLogger(__name__)

class ProposalEngine:
    def __init__(self, db_session, model_orch: ModelOrchestrator, project_root: str):
        self.db = db_session
        self.model_orch = model_orch
        self.project_root = project_root
        self.diagnosis_engine = DiagnosisEngine(model_orch, project_root)

    async def analyze_failures(self, window_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Scans OperationalIncidents and clusters them by type/pattern.
        Prioritizes Pilot Projects (Phase 15).
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        
        # 1. Fetch recent incidents with Project context
        stmt = (
            select(OperationalIncident)
            .where(OperationalIncident.status == "open")
            .where(OperationalIncident.created_at >= cutoff)
        )
        
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        
        if not rows:
            return []

        # 2. Clustering logic with Pilot awareness
        clusters = {}
        pilot_incidents = []

        for inc in rows:
            # We need to know if the project is pilot
            is_pilot = False
            if inc.project_id:
                project = await self.db.get(Project, inc.project_id)
                if project and project.is_pilot:
                    is_pilot = True

            if is_pilot:
                pilot_incidents.append(inc)
                continue

            # Cluster by type + first line of message (pattern extraction)
            first_line = inc.message.split("\n")[0][:60]
            key = f"{inc.incident_type}:{first_line}"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(inc)

        proposals = []

        # 3. Pilot failures trigger proposals IMMEDIATELY (High Priority)
        for inc in pilot_incidents:
            proposals.append({
                "title": f"PILOT CRITICAL: {inc.incident_type}",
                "description": f"Urgent investigation for Pilot Project incident: {inc.message[:200]}",
                "severity": "high",
                "source_type": "pilot_anomaly",
                "incidents": [str(inc.id)],
                "is_pilot": True,
                "project_id": inc.project_id
            })

        # 4. Standard clustering for non-pilot (Threshold: 3 incidents)
        for key, group in clusters.items():
            if len(group) >= 3:
                proposals.append({
                    "title": f"Autonomic fix for repetitive {group[0].incident_type}",
                    "description": f"Detected {len(group)} similar incidents. Pattern: {group[0].message[:100]}...",
                    "severity": "medium",
                    "source_type": "anomaly_cluster",
                    "incidents": [str(i.id) for i in group],
                    "is_pilot": False,
                    "project_id": None
                })

        return proposals

    async def generate_fix_proposal(self, incident_id: UUID) -> Optional[SystemImprovement]:
        """
        Generates a detailed fix proposal (SystemImprovement) for a single incident.
        Used primarily for Pilot Projects in the auto-fix loop.
        """
        incident = await self.db.get(OperationalIncident, incident_id)
        if not incident:
            return None

        # 1. Diagnose
        target_file, instruction = await self.diagnosis_engine.diagnose(
            incident_id=str(incident.id),
            incident_type=incident.incident_type,
            message=incident.message,
            payload=incident.payload or {}
        )

        if not target_file:
            logger.warning(f"Diagnosis failed for {incident.id}")
            return None

        # 2. Generate the actual code/diff (Proposed Patch)
        # We'll use the LLM to generate just the patch part
        prompt = f"""
SEN BİR SİSTEM OTONOM YAMA MOTORUSUN (PATCH GENERATOR).
HEDEF DOSYA: {target_file}
DÜZELTME TALİMATI: {instruction}

TALİMATI UYGULAYACAK BİR 'UNIFIED DIFF' ÜRET. 
SADECE DIFF ÇIKTISINI DÖNDÜR, AÇIKLAMA YAPMA.
"""
        response = await self.model_orch.complete(
            messages=[{"role": "user", "content": prompt}],
            preferred_agent="engineering-python-specialist"
        )
        patch_text = getattr(response, "content", str(response))

        # 3. Create SystemImprovement record
        improvement = SystemImprovement(
            id=uuid4(),
            target_file=target_file,
            instruction=instruction,
            proposed_patch=patch_text,
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(improvement)
        await self.db.commit()
        await self.db.refresh(improvement)
        
        return improvement

    async def create_improvement_opportunity(self, proposal: Dict[str, Any]) -> UUID:
        """Persists a clustered proposal as an ImprovementOpportunity."""
        opp = ImprovementOpportunity(
            id=uuid4(),
            source_type=proposal["source_type"],
            title=proposal["title"],
            description=proposal["description"],
            severity=proposal["severity"],
            status="open",
            evidence_detail=f"Linked Incidents: {', '.join(proposal['incidents'])}"
        )
        self.db.add(opp)
        await self.db.commit()
        return opp.id
