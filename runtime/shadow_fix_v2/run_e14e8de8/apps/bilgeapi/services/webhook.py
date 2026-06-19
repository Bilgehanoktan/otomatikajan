import asyncio
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from apps.bilgeapi.config import settings
from apps.bilgeapi.adapters.webhook import WebhookDispatcher, is_ssrf_safe
from apps.bilgeapi.repositories.interface import (
    WebhookDeliveryRepository, RepairRequestRepository, IncidentRepository, DiagnosticRepository
)
from apps.bilgeapi.schemas.repair import ApprovalStatus, DispatchStatus
from apps.bilgeapi.services.audit import AuditService

logger = logging.getLogger("bilgeapi.webhook_service")

# Module-level set for tracking background dispatch tasks (used by graceful shutdown)
background_tasks: set = set()


def _track_task(task: asyncio.Task) -> None:
    """Register a background task and auto-remove it when done."""
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


class WebhookDeliveryService:
    def __init__(
        self,
        webhook_repo: WebhookDeliveryRepository,
        repair_repo: RepairRequestRepository,
        incident_repo: Optional[IncidentRepository] = None,
        diagnostic_repo: Optional[DiagnosticRepository] = None,
        audit_service: Optional[AuditService] = None,
        dispatcher: Optional[WebhookDispatcher] = None
    ):
        self.webhook_repo = webhook_repo
        self.repair_repo = repair_repo
        self.incident_repo = incident_repo
        self.diagnostic_repo = diagnostic_repo
        self.audit_service = audit_service
        self.dispatcher = dispatcher or WebhookDispatcher()
        
        # Import registry locally to avoid circular dependencies
        from apps.bilgeapi.adapters.registry import adapter_registry
        self.registry = adapter_registry

    async def dispatch_webhook(
        self,
        repair_request_id: str,
        webhook_url: Optional[str],
        payload: dict,
        adapter: str = "webhook",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Initiates the delivery/dispatch workflow for the chosen adapter.
        """
        # Enrichment: Load diagnostic and incident metadata to inject into payload
        try:
            if self.repair_repo and self.diagnostic_repo and self.incident_repo:
                repair_req = await self.repair_repo.get(repair_request_id)
                if repair_req:
                    diag = await self.diagnostic_repo.get(repair_req.diagnostic_id)
                    if diag:
                        payload["diagnostic"] = {
                            "diagnostic_id": diag.diagnostic_id,
                            "incident_id": diag.incident_id,
                            "status": str(diag.status),
                            "summary": diag.summary,
                            "root_cause_hypothesis": diag.root_cause_hypothesis,
                            "confidence": diag.confidence,
                            "risk_score": diag.risk_score,
                            "recommendations": [
                                {"id": r.get("id") or r.get("recommendation_id"), "description": r.get("description")} 
                                for r in (diag.recommendations or [])
                            ]
                        }
                        inc = await self.incident_repo.get(diag.incident_id)
                        if inc:
                            payload["incident"] = {
                                "id": inc.id,
                                "project_key": inc.project_key,
                                "source_system": inc.source_system,
                                "environment": inc.environment,
                                "kind": inc.kind,
                                "severity": str(inc.severity),
                                "error_message": inc.error_message
                            }
        except Exception as e:
            logger.warning(f"Failed to enrich payload during dispatch: {e}")

        payload_str = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        delivery_data = {
            "repair_request_id": repair_request_id,
            "webhook_url": webhook_url or f"adapter:{adapter}",
            "status_code": None,
            "delivery_status": "PENDING",
            "error_message": None,
            "payload_hash": payload_hash,
            "attempt_count": 1.0
        }

        # Persist the initial delivery record
        delivery = await self.webhook_repo.create_delivery(delivery_data)

        # Trigger background delivery workflow
        if settings.BILGEAPI_DURABLE_QUEUE_ENABLED:
            from libs.queue_abstractions.job_queue import job_queue
            # Enqueue the job
            await job_queue.enqueue(
                "bilgeapi_webhook_delivery",
                delivery_id=delivery["id"],
                repair_request_id=repair_request_id,
                webhook_url=webhook_url or f"adapter:{adapter}",
                payload=payload,
                attempt=1,
                adapter=adapter,
                dry_run=dry_run
            )
        else:
            task = asyncio.create_task(
                self._execute_delivery(
                    delivery_id=delivery["id"],
                    repair_request_id=repair_request_id,
                    webhook_url=webhook_url or f"adapter:{adapter}",
                    payload=payload,
                    attempt=1,
                    adapter=adapter,
                    dry_run=dry_run
                )
            )
            _track_task(task)

        return delivery

    async def _execute_delivery(
        self,
        delivery_id: str,
        repair_request_id: str,
        webhook_url: str,
        payload: dict,
        attempt: int,
        adapter: str = "webhook",
        dry_run: bool = False
    ):
        """
        Executes dispatch using the selected adapter, updates DB state, and triggers retries if applicable.
        """
        adapter_obj = self.registry.get_adapter(adapter)
        if not adapter_obj:
            err_msg = f"Adapter '{adapter}' is not registered."
            logger.error(err_msg)
            await self._record_failure(delivery_id, repair_request_id, attempt, err_msg, adapter)
            return

        if not adapter_obj.enabled:
            err_msg = f"Adapter '{adapter}' is disabled."
            logger.error(err_msg)
            await self._record_failure(delivery_id, repair_request_id, attempt, err_msg, adapter)
            return

        is_webhook_with_dynamic_url = (adapter == "webhook" and bool(webhook_url))
        if not adapter_obj.configured and not is_webhook_with_dynamic_url:
            err_msg = f"Adapter '{adapter}' is not configured."
            logger.error(err_msg)
            await self._record_failure(delivery_id, repair_request_id, attempt, err_msg, adapter)
            return

        max_retries = settings.BILGEAPI_WEBHOOK_MAX_RETRIES

        try:
            logger.info(f"Attempting dispatch (id={delivery_id}, adapter={adapter}, attempt={attempt})")
            
            if adapter == "webhook":
                result = await adapter_obj.dispatch(
                    repair_request_id=repair_request_id,
                    payload=payload,
                    dry_run=dry_run,
                    webhook_url=webhook_url,
                    dispatcher=self.dispatcher
                )
            else:
                result = await adapter_obj.dispatch(
                    repair_request_id=repair_request_id,
                    payload=payload,
                    dry_run=dry_run
                )

            status = result.get("status")
            ext_ref = result.get("external_reference")
            err_msg = result.get("error_message")

            if status == "SENT":
                # SUCCESS
                await self.webhook_repo.update_delivery(
                    delivery_id=delivery_id,
                    delivery_status="SENT",
                    status_code=200.0,
                    error_message=None,
                    attempt_count=attempt
                )

                await self.repair_repo.update(
                    repair_request_id=repair_request_id,
                    approval_status=ApprovalStatus.APPROVED,
                    dispatch_status=DispatchStatus.DISPATCHED,
                    external_reference=ext_ref
                )

                await self.audit_service.log_event(
                    event_type="REPAIR_DISPATCHED",
                    actor_id="system",
                    actor_type="service",
                    entity_type="repair_request",
                    entity_id=repair_request_id,
                    metadata={"delivery_id": delivery_id, "adapter": adapter, "external_reference": ext_ref}
                )

                await self.audit_service.log_event(
                    event_type="WEBHOOK_SENT",
                    actor_id="system",
                    actor_type="service",
                    entity_type="webhook_delivery",
                    entity_id=delivery_id,
                    metadata={"status_code": 200, "repair_request_id": repair_request_id, "adapter": adapter}
                )
                logger.info(f"Dispatch succeeded (id={delivery_id}, adapter={adapter})")
                return
            else:
                # Adapter returned FAILED status (e.g. SSRF Guard, configuration error)
                # We fail immediately without scheduling a retry
                await self._record_failure(delivery_id, repair_request_id, attempt, err_msg or "Dispatch failed.", adapter)
                return

        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Dispatch attempt {attempt} failed (id={delivery_id}, adapter={adapter}): {err_msg}")
            
            # Only retry webhook; other adapters do not retry to avoid duplicate tickets/issues
            if adapter == "webhook" and attempt < max_retries:
                await self.webhook_repo.update_delivery(
                    delivery_id=delivery_id,
                    delivery_status="FAILED",
                    status_code=None,
                    error_message=err_msg,
                    attempt_count=attempt
                )

                await self.audit_service.log_event(
                    event_type="WEBHOOK_FAILED",
                    actor_id="system",
                    actor_type="service",
                    entity_type="webhook_delivery",
                    entity_id=delivery_id,
                    metadata={"reason": err_msg, "attempt": attempt, "repair_request_id": repair_request_id, "adapter": adapter}
                )

                # Schedule retry with backoff
                delay = float(settings.BILGEAPI_WEBHOOK_BACKOFF_FACTOR ** attempt)
                logger.info(f"Scheduling retry for webhook delivery {delivery_id} in {delay} seconds.")
                retry_task = asyncio.create_task(
                    self._retry_after_delay(
                        delay=delay,
                        delivery_id=delivery_id,
                        repair_request_id=repair_request_id,
                        webhook_url=webhook_url,
                        payload=payload,
                        next_attempt=attempt + 1,
                        adapter=adapter,
                        dry_run=dry_run
                    )
                )
                _track_task(retry_task)
            else:
                # Limit exceeded or non-webhook adapter -> Move directly to DEAD_LETTER
                await self._record_failure(delivery_id, repair_request_id, attempt, err_msg, adapter)

    async def _record_failure(self, delivery_id: str, repair_request_id: str, attempt: int, err_msg: str, adapter: str = "webhook"):
        await self.webhook_repo.update_delivery(
            delivery_id=delivery_id,
            delivery_status="DEAD_LETTER",
            status_code=None,
            error_message=err_msg,
            attempt_count=attempt
        )

        await self.repair_repo.update(
            repair_request_id=repair_request_id,
            approval_status=ApprovalStatus.APPROVED,
            dispatch_status=DispatchStatus.FAILED,
            external_reference=None
        )

        await self.audit_service.log_event(
            event_type="REPAIR_DISPATCH_FAILED",
            actor_id="system",
            actor_type="service",
            entity_type="repair_request",
            entity_id=repair_request_id,
            metadata={"reason": err_msg, "adapter": adapter}
        )

        await self.audit_service.log_event(
            event_type="WEBHOOK_DEAD_LETTER",
            actor_id="system",
            actor_type="service",
            entity_type="webhook_delivery",
            entity_id=delivery_id,
            metadata={"reason": err_msg, "repair_request_id": repair_request_id, "adapter": adapter}
        )
        logger.error(f"Dispatch failed permanently (id={delivery_id}, attempts={attempt}, adapter={adapter})")

    async def _retry_after_delay(
        self,
        delay: float,
        delivery_id: str,
        repair_request_id: str,
        webhook_url: str,
        payload: dict,
        next_attempt: int,
        adapter: str = "webhook",
        dry_run: bool = False
    ):
        await asyncio.sleep(delay)
        if settings.BILGEAPI_DURABLE_QUEUE_ENABLED:
            from libs.queue_abstractions.job_queue import job_queue
            await job_queue.enqueue(
                "bilgeapi_webhook_delivery",
                delivery_id=delivery_id,
                repair_request_id=repair_request_id,
                webhook_url=webhook_url,
                payload=payload,
                attempt=next_attempt,
                adapter=adapter,
                dry_run=dry_run
            )
        else:
            await self._execute_delivery(
                delivery_id=delivery_id,
                repair_request_id=repair_request_id,
                webhook_url=webhook_url,
                payload=payload,
                attempt=next_attempt,
                adapter=adapter,
                dry_run=dry_run
            )

async def run_webhook_dispatch_job(
    delivery_id: str,
    repair_request_id: str,
    webhook_url: str,
    payload: dict,
    attempt: int,
    adapter: str,
    dry_run: bool
):
    from libs.db.session import AsyncSessionLocal
    from apps.bilgeapi.repositories.postgres import (
        PostgresIncidentRepository, PostgresDiagnosticRepository, PostgresRepairRequestRepository,
        PostgresAuditRepository, PostgresWebhookDeliveryRepository
    )
    from apps.bilgeapi.services.audit import AuditService
    from apps.bilgeapi.services.webhook import WebhookDeliveryService

    async with AsyncSessionLocal() as db:
        webhook_repo = PostgresWebhookDeliveryRepository(db)
        repair_repo = PostgresRepairRequestRepository(db)
        incident_repo = PostgresIncidentRepository(db)
        diagnostic_repo = PostgresDiagnosticRepository(db)
        audit_repo = PostgresAuditRepository(db)
        
        audit_service = AuditService(audit_repo)
        
        webhook_service = WebhookDeliveryService(
            webhook_repo=webhook_repo,
            repair_repo=repair_repo,
            incident_repo=incident_repo,
            diagnostic_repo=diagnostic_repo,
            audit_service=audit_service
        )
        
        await webhook_service._execute_delivery(
            delivery_id=delivery_id,
            repair_request_id=repair_request_id,
            webhook_url=webhook_url,
            payload=payload,
            attempt=attempt,
            adapter=adapter,
            dry_run=dry_run
        )
