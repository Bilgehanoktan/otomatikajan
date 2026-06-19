import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from apps.bilgeapi.schemas.incident import IncidentCreate, IncidentResponse
from apps.bilgeapi.repositories.interface import IncidentRepository
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.routers.deps import get_incident_repository, get_audit_service
from apps.bilgeapi.auth import require_permission

router = APIRouter(prefix="/v1")

@router.post("/incidents", response_model=IncidentResponse, status_code=201, tags=["Incidents"])
async def create_incident(
    incident: IncidentCreate,
    incident_repo: IncidentRepository = Depends(get_incident_repository),
    audit_service: AuditService = Depends(get_audit_service),
    _identity: dict = Depends(require_permission("bilgeapi.incident.write"))
):
    # Auto-generate correlation_id if missing
    if not incident.correlation_id:
        incident.correlation_id = f"req_{uuid.uuid4().hex[:8]}"

    created_incident = await incident_repo.create(incident)
    
    # Audit log the creation
    await audit_service.log_event(
        event_type="INCIDENT_CREATED",
        actor_id=_identity["id"],
        actor_type=_identity["type"],
        entity_type="incident",
        entity_id=created_incident.id,
        correlation_id=created_incident.correlation_id,
        after_state=created_incident.model_dump(mode="json")
    )
    
    return created_incident

@router.get("/incidents", response_model=List[IncidentResponse], tags=["Incidents"])
async def list_incidents(
    project_key: Optional[str] = Query(None, description="Filter incidents by project key"),
    incident_repo: IncidentRepository = Depends(get_incident_repository),
    _identity: dict = Depends(require_permission("bilgeapi.incident.read"))
):
    return await incident_repo.list_all(project_key=project_key)

@router.get("/incidents/{incident_id}", response_model=IncidentResponse, tags=["Incidents"])
async def get_incident(
    incident_id: str,
    incident_repo: IncidentRepository = Depends(get_incident_repository),
    _identity: dict = Depends(require_permission("bilgeapi.incident.read"))
):
    incident = await incident_repo.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

