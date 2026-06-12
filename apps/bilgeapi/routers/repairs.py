import socket
from typing import List, Optional
from urllib.parse import urlparse
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.bilgeapi.config import settings
from apps.bilgeapi.auth import require_permission
from apps.bilgeapi.schemas.repair import (
    RepairRequestCreate, RepairRequestResponse, RepairApprovalRequest, 
    RepairRejectionRequest, ApprovalStatus, DispatchStatus, RepairDispatchRequest
)
from apps.bilgeapi.schemas.webhook import WebhookTestRequest, WebhookTestResponse, WebhookDeliveryResponse
from apps.bilgeapi.repositories.interface import (
    RepairRequestRepository, WebhookDeliveryRepository, DiagnosticRepository, IncidentRepository
)
from apps.bilgeapi.services.webhook import WebhookDeliveryService
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.services.risk import RiskScoringService
from apps.bilgeapi.adapters.webhook import is_ssrf_safe, generate_signature
from apps.bilgeapi.routers.deps import (
    get_repair_repository, get_webhook_repository, get_webhook_service, get_audit_service,
    get_risk_scoring_service, get_diagnostic_repository, get_incident_repository
)

router = APIRouter(prefix="/v1")

@router.post("/repair-requests", response_model=RepairRequestResponse, status_code=201, tags=["Repairs"])
async def create_repair_request(
    diagnostic_id: str = Query(..., description="The associated diagnostic ID"),
    request: RepairRequestCreate = Depends(),
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    _identity: dict = Depends(require_permission("bilgeapi.incident.write"))
):
    """
    Creates a pending repair request for a diagnostic run.
    """
    created_request = await repair_repo.create(diagnostic_id, request)
    return created_request

@router.post("/repair-requests/json", response_model=RepairRequestResponse, status_code=201, tags=["Repairs"])
async def create_repair_request_json(
    diagnostic_id: str,
    request: RepairRequestCreate,
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    _identity: dict = Depends(require_permission("bilgeapi.incident.write"))
):
    """
    Creates a pending repair request using JSON body.
    """
    created_request = await repair_repo.create(diagnostic_id, request)
    return created_request

@router.post("/diagnostics/{diagnostic_id}/repair-requests", response_model=RepairRequestResponse, status_code=201, tags=["Repairs"])
async def create_repair_request_from_diagnostic(
    diagnostic_id: str,
    requested_by: Optional[str] = Query(None, description="Optional custom requested_by, defaults to authenticated user ID"),
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    diagnostic_repo: DiagnosticRepository = Depends(get_diagnostic_repository),
    incident_repo: IncidentRepository = Depends(get_incident_repository),
    risk_service: RiskScoringService = Depends(get_risk_scoring_service),
    audit_service: AuditService = Depends(get_audit_service),
    _identity: dict = Depends(require_permission("bilgeapi.incident.write"))
):
    """
    Creates a repair request by evaluating the diagnostic run results and calculating deterministic risk.
    """
    # 1. Fetch diagnostic run
    diagnostic_run = await diagnostic_repo.get(diagnostic_id)
    if not diagnostic_run:
        raise HTTPException(status_code=404, detail="Diagnostic run not found")

    if diagnostic_run.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Only completed diagnostics can trigger repair requests")

    # 2. Fetch associated incident
    incident = await incident_repo.get(diagnostic_run.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found for this diagnostic run")

    # 3. Calculate risk score & reasons
    risk_score, risk_reason = risk_service.calculate_risk(incident, diagnostic_run)

    # 4. Formulate policy logic
    is_low_risk = risk_score < 0.3
    is_prod = incident.environment.lower() == "production"
    is_sensitive = ("security" in risk_reason.lower() or 
                    "database" in risk_reason.lower() or 
                    "workflow" in risk_reason.lower())

    if is_low_risk and not is_prod and not is_sensitive:
        approval_required = False
        approval_status = ApprovalStatus.APPROVED
        approved_by = "system"
        approved_at = datetime.now(timezone.utc)
    else:
        approval_required = True
        approval_status = ApprovalStatus.PENDING
        approved_by = None
        approved_at = None

    # 5. Save the repair request
    requested_by_val = requested_by if requested_by else _identity["id"]
    create_schema = RepairRequestCreate(
        requested_by=requested_by_val,
        risk_score=risk_score,
        risk_reason=risk_reason,
        approval_required=approval_required,
        approval_status=approval_status,
        approved_by=approved_by,
        approved_at=approved_at
    )

    created_req = await repair_repo.create(diagnostic_id, create_schema)

    # 6. Audit Logging
    await audit_service.log_event(
        event_type="REPAIR_REQUEST_CREATED",
        actor_id=_identity["id"],
        actor_type=_identity["type"],
        entity_type="repair_request",
        entity_id=created_req.id,
        correlation_id=incident.correlation_id,
        after_state=created_req.model_dump(mode="json")
    )

    await audit_service.log_event(
        event_type="REPAIR_RISK_SCORED",
        actor_id="system",
        actor_type="service",
        entity_type="repair_request",
        entity_id=created_req.id,
        correlation_id=incident.correlation_id,
        metadata={"risk_score": risk_score, "risk_reason": risk_reason}
    )

    if not approval_required:
        await audit_service.log_event(
            event_type="REPAIR_APPROVED",
            actor_id="system",
            actor_type="service",
            entity_type="repair_request",
            entity_id=created_req.id,
            correlation_id=incident.correlation_id,
            metadata={"reason": "Auto-approved low risk change"}
        )

    return created_req

@router.get("/repair-requests", response_model=List[RepairRequestResponse], tags=["Repairs"])
async def list_repair_requests(
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    _identity: dict = Depends(require_permission("bilgeapi.incident.read"))
):
    """
    Lists all repair requests.
    """
    return await repair_repo.list_all()

@router.get("/repair-requests/{id}", response_model=RepairRequestResponse, tags=["Repairs"])
async def get_repair_request(
    id: str,
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    _identity: dict = Depends(require_permission("bilgeapi.incident.read"))
):
    """
    Retrieves a single repair request by ID.
    """
    repair_req = await repair_repo.get(id)
    if not repair_req:
        raise HTTPException(status_code=404, detail="Repair request not found")
    return repair_req

@router.post("/repair-requests/{id}/approve", response_model=RepairRequestResponse, tags=["Repairs"])
async def approve_repair_request(
    id: str,
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    audit_service: AuditService = Depends(get_audit_service),
    _identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Approves a repair request. Does not dispatch webhook.
    """
    repair_req = await repair_repo.get(id)
    if not repair_req:
        raise HTTPException(status_code=404, detail="Repair request not found")

    if repair_req.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot approve repair request in state {repair_req.approval_status}")

    updated_req = await repair_repo.update(
        repair_request_id=id,
        approval_status=ApprovalStatus.APPROVED,
        dispatch_status=repair_req.dispatch_status,
        approved_by=_identity["id"],
        approved_at=datetime.now(timezone.utc)
    )

    await audit_service.log_event(
        event_type="REPAIR_APPROVED",
        actor_id=_identity["id"],
        actor_type=_identity["type"],
        entity_type="repair_request",
        entity_id=id,
        metadata={"approved_by": _identity["id"]}
    )

    return updated_req

@router.post("/repair-requests/{id}/reject", response_model=RepairRequestResponse, tags=["Repairs"])
async def reject_repair_request(
    id: str,
    rejection: RepairRejectionRequest,
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    audit_service: AuditService = Depends(get_audit_service),
    _identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Rejects a repair request with a reason.
    """
    repair_req = await repair_repo.get(id)
    if not repair_req:
        raise HTTPException(status_code=404, detail="Repair request not found")

    if repair_req.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot reject repair request in state {repair_req.approval_status}")

    updated_req = await repair_repo.update(
        repair_request_id=id,
        approval_status=ApprovalStatus.REJECTED,
        dispatch_status=repair_req.dispatch_status,
        rejection_reason=rejection.rejection_reason,
        rejected_at=datetime.now(timezone.utc)
    )

    await audit_service.log_event(
        event_type="REPAIR_REJECTED",
        actor_id=_identity["id"],
        actor_type=_identity["type"],
        entity_type="repair_request",
        entity_id=id,
        metadata={"rejection_reason": rejection.rejection_reason}
    )

    return updated_req

@router.post("/repair-requests/{id}/dispatch", response_model=RepairRequestResponse, tags=["Repairs"])
async def dispatch_repair_request(
    id: str,
    dispatch_req: Optional[RepairDispatchRequest] = None,
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    webhook_service: WebhookDeliveryService = Depends(get_webhook_service),
    audit_service: AuditService = Depends(get_audit_service),
    _identity: dict = Depends(require_permission("bilgeapi.incident.write"))
):
    """
    Dispatches the approved (or auto-approved) repair request to the target webhook.
    """
    repair_req = await repair_repo.get(id)
    if not repair_req:
        raise HTTPException(status_code=404, detail="Repair request not found")

    # Dispatch constraint check
    if repair_req.approval_required and repair_req.approval_status != ApprovalStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Cannot dispatch unapproved repair request")

    if repair_req.approval_status == ApprovalStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Cannot dispatch rejected repair request")

    if repair_req.dispatch_status == DispatchStatus.DISPATCHED:
        raise HTTPException(status_code=400, detail="Repair request has already been dispatched")

    adapter = "webhook"
    webhook_url = None
    dry_run = False

    if dispatch_req:
        adapter = dispatch_req.adapter
        webhook_url = dispatch_req.webhook_url
        dry_run = dispatch_req.dry_run

    supported_adapters = {"webhook", "github_issue", "jira", "sovereign_repair_lab"}
    if adapter not in supported_adapters:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported dispatch adapter: '{adapter}'. Supported: {list(supported_adapters)}"
        )

    if adapter == "webhook":
        webhook_url = webhook_url if webhook_url else settings.BILGEAPI_WEBHOOK_URL
        if not webhook_url:
            raise HTTPException(
                status_code=400,
                detail="Webhook URL has not been provided and is not configured in settings."
            )

    # Format webhook payload
    payload = {
        "event": "repair.dispatched",
        "repair_request": {
            "id": repair_req.id,
            "diagnostic_id": repair_req.diagnostic_id,
            "requested_by": repair_req.requested_by,
            "approved_by": repair_req.approved_by,
            "approval_status": str(repair_req.approval_status),
            "risk_score": repair_req.risk_score,
            "risk_reason": repair_req.risk_reason,
            "dispatch_status": str(repair_req.dispatch_status),
            "approval_required": repair_req.approval_required,
            "rejection_reason": repair_req.rejection_reason,
            "approved_at": repair_req.approved_at.isoformat() if repair_req.approved_at else None,
            "rejected_at": repair_req.rejected_at.isoformat() if repair_req.rejected_at else None,
            "created_at": repair_req.created_at.isoformat(),
            "updated_at": repair_req.updated_at.isoformat()
        }
    }

    # Log dispatch requested audit event
    await audit_service.log_event(
        event_type="REPAIR_DISPATCH_REQUESTED",
        actor_id=_identity["id"],
        actor_type=_identity["type"],
        entity_type="repair_request",
        entity_id=id,
        metadata={"webhook_url": webhook_url, "adapter": adapter, "dry_run": dry_run}
    )

    # Trigger background dispatch
    await webhook_service.dispatch_webhook(
        repair_request_id=id,
        webhook_url=webhook_url,
        payload=payload,
        adapter=adapter,
        dry_run=dry_run
    )

    # Reload the latest state from repository
    return await repair_repo.get(id)

@router.get("/webhook-deliveries", response_model=List[WebhookDeliveryResponse], tags=["Webhooks"])
async def list_webhook_deliveries(
    webhook_repo: WebhookDeliveryRepository = Depends(get_webhook_repository),
    _identity: dict = Depends(require_permission("bilgeapi.audit.read"))
):
    """
    Retrieves all webhook delivery attempt logs.
    """
    deliveries = await webhook_repo.list_deliveries()
    mapped = []
    for d in deliveries:
        mapped.append(
            WebhookDeliveryResponse(
                id=d["id"],
                repair_request_id=d["repair_request_id"],
                webhook_url=d["webhook_url"],
                status_code=d.get("status_code"),
                delivery_status=d["delivery_status"],
                error_message=d.get("error_message"),
                payload_hash=d["payload_hash"],
                attempt_count=d["attempt_count"],
                created_at=d["created_at"]
            )
        )
    return mapped

@router.post("/webhooks/test", response_model=WebhookTestResponse, tags=["Webhooks"])
async def test_webhook(
    request: WebhookTestRequest,
    _identity: dict = Depends(require_permission("bilgeapi.admin"))
):
    """
    Sends a test payload to the target webhook URL using the full SSRF, signature, and timeout flow.
    """
    webhook_url = request.webhook_url
    allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS

    resolved_ip = None
    try:
        parsed = urlparse(webhook_url)
        if parsed.hostname:
            resolved_ip = socket.gethostbyname(parsed.hostname)
    except Exception:
        pass

    if not is_ssrf_safe(webhook_url, allow_private=allow_private):
        raise HTTPException(
            status_code=400,
            detail=f"SSRF Guard: Target URL {webhook_url} is forbidden."
        )

    test_payload = request.payload if request.payload else {"message": "Test webhook from BilgeAPI"}
    import json
    payload_str = json.dumps(test_payload)
    secret = settings.BILGEAPI_WEBHOOK_SECRET
    signature = generate_signature(payload_str, secret)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    idempotency_key = "test_idemp_key_123"

    try:
        headers = {
            "Content-Type": "application/json",
            "X-BilgeAPI-Signature": signature,
            "X-BilgeAPI-Timestamp": timestamp,
            "X-BilgeAPI-Idempotency-Key": idempotency_key
        }

        async with httpx.AsyncClient(timeout=settings.BILGEAPI_WEBHOOK_TIMEOUT, follow_redirects=False, max_redirects=0) as client:
            response = await client.post(webhook_url, content=payload_str, headers=headers, follow_redirects=False)

        status_code = response.status_code
        if 200 <= status_code < 300:
            return WebhookTestResponse(
                status="SENT",
                resolved_ip=resolved_ip,
                signature=signature,
                status_code=float(status_code),
                error_message=None,
                timestamp=timestamp,
                idempotency_key=idempotency_key
            )
        else:
            return WebhookTestResponse(
                status="FAILED",
                resolved_ip=resolved_ip,
                signature=signature,
                status_code=float(status_code),
                error_message=f"Received non-2xx status code: {status_code}",
                timestamp=timestamp,
                idempotency_key=idempotency_key
            )
    except Exception as e:
        return WebhookTestResponse(
            status="DEAD_LETTER",
            resolved_ip=resolved_ip,
            signature=signature,
            status_code=None,
            error_message=str(e),
            timestamp=timestamp,
            idempotency_key=idempotency_key
        )
