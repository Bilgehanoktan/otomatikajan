import asyncio
from datetime import datetime, timezone
import logging
from typing import Optional
from apps.bilgeapi.repositories.interface import (
    DiagnosticRepository, FindingRepository, RecommendationRepository, IncidentRepository
)
from apps.bilgeapi.adapters.mock_agent import MockAgentAdapter
from apps.bilgeapi.schemas.diagnostic import DiagnosticStatus, DiagnosticResult
from apps.bilgeapi.services.audit import AuditService

logger = logging.getLogger("bilgeapi.diagnostic")

background_tasks: set[asyncio.Task] = set()


def _track_task(task: asyncio.Task) -> None:
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


class DiagnosticService:
    def __init__(
        self,
        incident_repo: IncidentRepository,
        diagnostic_repo: DiagnosticRepository,
        finding_repo: FindingRepository,
        recommendation_repo: RecommendationRepository,
        audit_service: AuditService
    ):
        self.incident_repo = incident_repo
        self.diagnostic_repo = diagnostic_repo
        self.finding_repo = finding_repo
        self.recommendation_repo = recommendation_repo
        self.audit_service = audit_service
        self.mock_adapter = MockAgentAdapter()

    async def start_diagnostic(self, incident_id: str, tenant_id: str) -> Optional[DiagnosticResult]:
        if not tenant_id:
            raise ValueError("tenant_id is required")
        incident = await self.incident_repo.get(incident_id, tenant_id=tenant_id)
        if not incident:
            return None

        # Create diagnostic run in QUEUED state
        diag_run = await self.diagnostic_repo.create(incident_id, tenant_id=tenant_id)
        
        # Audit log the queue state
        await self.audit_service.log_event(
            event_type="DIAGNOSTIC_QUEUED",
            actor_id="system",
            actor_type="system",
            entity_type="diagnostic",
            entity_id=diag_run.diagnostic_id,
            tenant_id=tenant_id,
            correlation_id=incident.correlation_id,
            after_state=diag_run.model_dump(mode="json")
        )

        # Trigger background processing task
        task = asyncio.create_task(self._process_diagnostic(diag_run.diagnostic_id, incident_id, tenant_id))
        _track_task(task)
        
        return diag_run

    async def _process_diagnostic(self, diagnostic_id: str, incident_id: str, tenant_id: str):
        try:
            # 1. Transition status to RUNNING
            diag_run = await self.diagnostic_repo.update(diagnostic_id, DiagnosticStatus.RUNNING, tenant_id=tenant_id)
            incident = await self.incident_repo.get(incident_id, tenant_id=tenant_id)
            if not diag_run or not incident:
                return

            await self.audit_service.log_event(
                event_type="DIAGNOSTIC_RUNNING",
                actor_id="system",
                actor_type="system",
                entity_type="diagnostic",
                entity_id=diagnostic_id,
                tenant_id=tenant_id,
                correlation_id=incident.correlation_id,
                before_state={"status": "QUEUED"},
                after_state={"status": "RUNNING"}
            )

            # Simulate processing delay
            await asyncio.sleep(0.05)

            # 2. Invoke diagnostic adapter
            results = await self.mock_adapter.run_diagnostic(incident)

            # 3. Save findings and recommendations
            saved_findings = []
            for f in results.get("findings", []):
                saved_f = await self.finding_repo.create(diagnostic_id, f, tenant_id=tenant_id)
                saved_findings.append(saved_f)

            saved_recs = []
            for r in results.get("recommendations", []):
                saved_r = await self.recommendation_repo.create(diagnostic_id, r, tenant_id=tenant_id)
                saved_recs.append(saved_r)

            # 4. Transition status to COMPLETED
            completed_diag = await self.diagnostic_repo.update(
                diagnostic_id,
                DiagnosticStatus.COMPLETED,
                tenant_id=tenant_id,
                summary=results.get("summary"),
                root_cause_hypothesis=results.get("root_cause_hypothesis"),
                confidence=results.get("confidence"),
                risk_score=results.get("risk_score"),
                findings=saved_findings,
                recommendations=saved_recs
            )

            await self.audit_service.log_event(
                event_type="DIAGNOSTIC_COMPLETED",
                actor_id="system",
                actor_type="system",
                entity_type="diagnostic",
                entity_id=diagnostic_id,
                tenant_id=tenant_id,
                correlation_id=incident.correlation_id,
                before_state={"status": "RUNNING"},
                after_state=completed_diag.model_dump(mode="json")
            )

        except Exception as e:
            logger.error(f"Error processing diagnostic {diagnostic_id}: {e}", exc_info=True)
            failed_diag = await self.diagnostic_repo.update(diagnostic_id, DiagnosticStatus.FAILED, tenant_id=tenant_id)
            
            # Find correlation ID if possible
            correlation_id = None
            try:
                incident = await self.incident_repo.get(incident_id, tenant_id=tenant_id)
                if incident:
                    correlation_id = incident.correlation_id
            except Exception:
                pass

            await self.audit_service.log_event(
                event_type="DIAGNOSTIC_FAILED",
                actor_id="system",
                actor_type="system",
                entity_type="diagnostic",
                entity_id=diagnostic_id,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                before_state={"status": "RUNNING"},
                after_state={"status": "FAILED", "error": str(e)}
            )
