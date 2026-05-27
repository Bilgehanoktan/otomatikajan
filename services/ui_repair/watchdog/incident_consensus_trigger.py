# filepath: services/ui_repair/watchdog/incident_consensus_trigger.py
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

from libs.db.session import session_scope
from libs.db.models.core_models import OperationalIncident
from agents.meeting_room import MeetingRoom
from sqlalchemy import select

logger = logging.getLogger("ui_repair.watchdog.incident_consensus_trigger")

class IncidentConsensusTrigger:
    """
    Auto-Trigger Consensus Engine.
    Detects critical/high open operational incidents and automatically triggers
    a dynamic debate meeting to resolve them without human intervention.
    """

    def __init__(self, meeting_room: MeetingRoom = None):
        self.meeting_room = meeting_room or MeetingRoom()

    async def scan_and_resolve_incidents(self) -> List[Dict[str, Any]]:
        """
        Scans for open high/critical incidents, triggers dynamic consensus debate for each,
        and saves results directly to the database.
        """
        logger.info("[Consensus Trigger] Scanning for open critical/high operational incidents...")
        reports = []

        async with session_scope() as session:
            # Query for open high or critical incidents
            stmt = select(OperationalIncident).where(
                OperationalIncident.status == "open",
                OperationalIncident.severity.in_(["critical", "high"])
            )
            result = await session.execute(stmt)
            incidents = result.scalars().all()

            if not incidents:
                logger.info("[Consensus Trigger] No open critical/high incidents found.")
                return []

            logger.info(f"[Consensus Trigger] Found {len(incidents)} incident(s) needing auto-consensus.")

            for incident in incidents:
                logger.info(f"[Consensus Trigger] Processing Incident ID: {incident.id} ({incident.incident_type})")
                
                # Step 1: Mark as investigating
                incident.status = "investigating"
                await session.flush()

                # Step 2: Formulate proposal for debate
                proposal = f"Sistem Kritik Hata Sentezi | Tür: {incident.incident_type} | Mesaj: {incident.message}"
                
                try:
                    # Step 3: Run debate meeting
                    # Standard participants: architect, qa_engineer, security
                    debate_report = await self.meeting_room.hold_meeting(
                        proposal=proposal,
                        participant_ids=["architect", "qa_engineer", "security"]
                    )

                    # Step 4: Update incident with consensus results
                    # Merge existing payload with consensus report
                    payload = dict(incident.payload) if incident.payload else {}
                    payload["consensus_report"] = debate_report
                    incident.payload = payload
                    
                    incident.status = "resolved"
                    incident.resolved_at = datetime.now(timezone.utc)
                    
                    logger.info(f"[Consensus Trigger] Auto-Consensus completed. Decision: {debate_report['final_decision']}")
                    reports.append(debate_report)
                except Exception as e:
                    logger.error(f"[Consensus Trigger] Failed to hold debate for incident {incident.id}: {e}")
                    incident.status = "open"  # Rollback status to open so it can be retried
                
            await session.commit()
            
        return reports

if __name__ == "__main__":
    # Test execution block
    async def main():
        logging.basicConfig(level=logging.INFO)
        trigger = IncidentConsensusTrigger()
        await trigger.scan_and_resolve_incidents()
        
    asyncio.run(main())
