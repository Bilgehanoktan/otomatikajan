import asyncio
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from apps.bilgeapi.config import settings
from apps.bilgeapi.adapters.webhook import WebhookDispatcher, is_ssrf_safe
from apps.bilgeapi.repositories.interface import WebhookDeliveryRepository, RepairRequestRepository
from apps.bilgeapi.schemas.repair import ApprovalStatus, DispatchStatus
from apps.bilgeapi.services.audit import AuditService

logger = logging.getLogger("bilgeapi.webhook_service")

class WebhookDeliveryService:
    def __init__(
        self,
        webhook_repo: WebhookDeliveryRepository,
        repair_repo: RepairRequestRepository,
        audit_service: AuditService
    ):
        self.webhook_repo = webhook_repo
        self.repair_repo = repair_repo
        self.audit_service = audit_service
        self.dispatcher = WebhookDispatcher()

    async def dispatch_webhook(self, repair_request_id: str, webhook_url: str, payload: dict) -> Dict[str, Any]:
        """
        Initiates the webhook delivery workflow.
        Returns the initial pending delivery record representation.
        """
        payload_str = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

        delivery_data = {
            "repair_request_id": repair_request_id,
            "webhook_url": webhook_url,
            "status_code": None,
            "delivery_status": "PENDING",
            "error_message": None,
            "payload_hash": payload_hash,
            "attempt_count": 1.0
        }

        # Persist the initial delivery record
        delivery = await self.webhook_repo.create_delivery(delivery_data)

        # Trigger background delivery workflow
        asyncio.create_task(
            self._execute_delivery(
                delivery_id=delivery["id"],
                repair_request_id=repair_request_id,
                webhook_url=webhook_url,
                payload=payload,
                attempt=1
            )
        )

        return delivery

    async def _execute_delivery(
        self,
        delivery_id: str,
        repair_request_id: str,
        webhook_url: str,
        payload: dict,
        attempt: int
    ):
        """
        Executes the actual HTTP POST dispatch, handles errors, updates DB state, and triggers retries.
        """
        # Validate SSRF Guard
        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if not is_ssrf_safe(webhook_url, allow_private=allow_private):
            err_msg = f"SSRF Guard: URL {webhook_url} is forbidden."
            logger.error(err_msg)
            
            # Transition directly to FAILED/DEAD_LETTER since SSRF is non-recoverable
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
                metadata={"reason": err_msg}
            )

            await self.audit_service.log_event(
                event_type="WEBHOOK_DEAD_LETTER",
                actor_id="system",
                actor_type="service",
                entity_type="webhook_delivery",
                entity_id=delivery_id,
                metadata={"reason": err_msg, "repair_request_id": repair_request_id}
            )
            return

        idempotency_key = f"idemp_{delivery_id}"
        timestamp = datetime.now(timezone.utc).isoformat()
        max_retries = settings.BILGEAPI_WEBHOOK_MAX_RETRIES
        secret = settings.BILGEAPI_WEBHOOK_SECRET

        try:
            logger.info(f"Attempting webhook delivery (id={delivery_id}, attempt={attempt}) to {webhook_url}")
            response = await self.dispatcher.dispatch(
                url=webhook_url,
                payload=payload,
                signature_secret=secret,
                idempotency_key=idempotency_key,
                timestamp=timestamp
            )

            status_code = float(response.status_code)
            
            if 200 <= status_code < 300:
                # SUCCESS
                await self.webhook_repo.update_delivery(
                    delivery_id=delivery_id,
                    delivery_status="SENT",
                    status_code=status_code,
                    error_message=None,
                    attempt_count=attempt
                )

                await self.repair_repo.update(
                    repair_request_id=repair_request_id,
                    approval_status=ApprovalStatus.APPROVED,
                    dispatch_status=DispatchStatus.DISPATCHED,
                    external_reference=f"web_{delivery_id}"
                )

                await self.audit_service.log_event(
                    event_type="REPAIR_DISPATCHED",
                    actor_id="system",
                    actor_type="service",
                    entity_type="repair_request",
                    entity_id=repair_request_id,
                    metadata={"delivery_id": delivery_id}
                )

                await self.audit_service.log_event(
                    event_type="WEBHOOK_SENT",
                    actor_id="system",
                    actor_type="service",
                    entity_type="webhook_delivery",
                    entity_id=delivery_id,
                    metadata={"status_code": status_code, "repair_request_id": repair_request_id}
                )
                logger.info(f"Webhook delivery succeeded (id={delivery_id}, code={status_code})")
                return
            else:
                # HTTP Failure (e.g. 500, 404, or 3xx redirection)
                err_msg = f"HTTP Error Status Code: {status_code}"
                raise Exception(err_msg)

        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Webhook attempt {attempt} failed (id={delivery_id}): {err_msg}")
            
            # Check for retry availability
            if attempt < max_retries:
                # Transition to FAILED state but schedule retry
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
                    metadata={"reason": err_msg, "attempt": attempt, "repair_request_id": repair_request_id}
                )

                # Schedule retry with backoff
                delay = float(settings.BILGEAPI_WEBHOOK_BACKOFF_FACTOR ** attempt)
                logger.info(f"Scheduling retry for webhook delivery {delivery_id} in {delay} seconds.")
                asyncio.create_task(
                    self._retry_after_delay(
                        delay=delay,
                        delivery_id=delivery_id,
                        repair_request_id=repair_request_id,
                        webhook_url=webhook_url,
                        payload=payload,
                        next_attempt=attempt + 1
                    )
                )
            else:
                # Limit exceeded -> Move to DEAD_LETTER
                await self.webhook_repo.update_delivery(
                    delivery_id=delivery_id,
                    delivery_status="DEAD_LETTER",
                    status_code=None,
                    error_message=f"Max retries reached. Last error: {err_msg}",
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
                    metadata={"reason": f"Max retries reached. Last: {err_msg}"}
                )

                await self.audit_service.log_event(
                    event_type="WEBHOOK_DEAD_LETTER",
                    actor_id="system",
                    actor_type="service",
                    entity_type="webhook_delivery",
                    entity_id=delivery_id,
                    metadata={"reason": f"Max retries reached. Last: {err_msg}", "repair_request_id": repair_request_id}
                )
                logger.error(f"Webhook delivery failed permanently (id={delivery_id}, attempts={attempt})")

    async def _retry_after_delay(
        self,
        delay: float,
        delivery_id: str,
        repair_request_id: str,
        webhook_url: str,
        payload: dict,
        next_attempt: int
    ):
        await asyncio.sleep(delay)
        await self._execute_delivery(
            delivery_id=delivery_id,
            repair_request_id=repair_request_id,
            webhook_url=webhook_url,
            payload=payload,
            attempt=next_attempt
        )
