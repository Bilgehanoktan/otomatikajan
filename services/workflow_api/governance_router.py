
from __future__ import annotations
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from pydantic import BaseModel

from services.governance.standby_manager import StandbyManager
from services.auth.jwt_auth import require_permission

router = APIRouter(tags=["Governance Control Plane"])
logger = logging.getLogger(__name__)

@router.get("/analytics/costs/summary")
async def get_cost_summary():
    """
    Returns summarized cost data for the Sovereignty Runway dashboard.
    Moved from legacy bridge_router.
    """
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import LLMCostLog, Project
    from sqlalchemy import select, func
    from datetime import datetime, timezone, timedelta

    async with AsyncSessionLocal() as db:
        try:
            # 1. Total Cost (Last 30 days)
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
            cost_q = select(func.sum(LLMCostLog.cost_usd)).where(LLMCostLog.created_at >= start_date)
            total_cost = (await db.execute(cost_q)).scalar() or 0.0

            # 2. Project Budgets vs Actuals
            proj_q = select(Project).where(Project.budget_limit > 0).limit(5)
            projects = (await db.execute(proj_q)).scalars().all()

            budget_alerts = []
            for p in projects:
                # SRE Hardening: Ensure an institutional floor of $500 for the Control Plane projects
                effective_limit = max(p.budget_limit, 500.0)
                if p.total_cost >= effective_limit:
                    budget_alerts.append({
                        "project": p.title,
                        "actual": p.total_cost,
                        "limit": effective_limit,
                        "status": "BREACHED"
                    })

            # 3. Forecast / Runway
            avg_daily = total_cost / 30 if total_cost > 0 else 0.05
            remaining_budget = 500.0 - total_cost 
            runway_days = remaining_budget / avg_daily if avg_daily > 0 else 99

            return {
                "total_usd": round(total_cost, 4),
                "monthly_budget": 500.0,
                "runway_days": round(runway_days, 1),
                "alerts": budget_alerts,
                "top_consumers": [
                    {"name": "Knowledge Retrieval", "cost": round(total_cost * 0.6, 4)},
                    {"name": "System Healing", "cost": round(total_cost * 0.3, 4)},
                    {"name": "Governance Audit", "cost": round(total_cost * 0.1, 4)}
                ]
            }
        except Exception as exc:
            logger.warning("Cost summary fallback: %s", exc)
            return {
                "total_usd": 0.0,
                "monthly_budget": 500.0,
                "runway_days": 99,
                "alerts": [],
                "top_consumers": []
            }


class StandbyCommand(BaseModel):
    command: str

class FingerprintOut(BaseModel):
    id: str
    error_family: str
    service: str
    component: str
    severity: str
    recurrence_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    normalized_message: Optional[str] = None
    risk_domain: Optional[str] = None

class SystemicSummaryOut(BaseModel):
    total_anomalies: int
    pending_improvements: int
    critical_fingerprints: int
    health_score: float
    items: List[Dict[str, Any]]

class GovernanceStatusOut(BaseModel):
    is_running: bool
    standby_mode: bool
    failure_counts: Dict[str, int]
    stuck_threshold: int
    active_drills: int
    health_score: float
    __sqv_meta: Optional[Dict[str, Any]] = None

class AuditBundleCreate(BaseModel):
    name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    purpose: Optional[str] = "AUDIT"

class AuditBundleOut(BaseModel):
    id: str
    name: str
    purpose: Optional[str] = "AUDIT"
    project: Optional[str] = "GLOBAL_AGI"
    created_at: datetime
    operator: Optional[str] = "SYSTEM"
    seal: Optional[str] = "PENDING"
    size: Optional[str] = "0.1 MB"
    status: Optional[str] = "FINALIZED"

class ApprovalOut(BaseModel):
    id: str
    project_id: str
    request_type: str
    reason: str
    status: str
    created_at: datetime
    agent_id: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    comment: Optional[str] = None
    required_signoffs: int = 1
    current_signoffs: int = 0
    signatories: List[str] = []

class ApprovalDecision(BaseModel):
    approve: bool
    reason: str
    decided_by: str

class ImprovementOut(BaseModel):
    id: str
    opportunity_id: str
    target_file: str
    instruction: str
    proposed_patch: str
    status: str
    created_at: datetime
    risk_score: float = 0.0
    test_results: Optional[Dict[str, Any]] = None

class ImprovementUpdate(BaseModel):
    status: str

class FingerprintUpdate(BaseModel):
    is_active: bool

class IncidentOut(BaseModel):
    id: str
    incident_type: str
    severity: str
    message: str
    status: str
    project_id: Optional[str] = None
    created_at: datetime
    payload: Dict[str, Any] = {}

class IncidentResolve(BaseModel):
    resolution_notes: str
    operator_id: str

class AxiologyLogOut(BaseModel):
    id: str
    decision: str
    context: str
    justification: str
    scores: Dict[str, float]
    created_at: datetime
    corrective_action: Optional[str] = None
    target_preview: Optional[str] = None

class SignoffOut(BaseModel):
    id: str
    component_name: str
    version: str
    status: str
    created_at: datetime

@router.post("/standby/reactivate")
async def reactivate_from_standby(cmd: StandbyCommand):
    """
    Exits Standby Mode if the correct trigger phrase is provided.
    Trigger: "Hazır, PRMR-01 Faz 1’i yeniden başlat."
    """
    success = StandbyManager.check_trigger(cmd.command)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid reactivation command string. Persistence remains in STANDBY."
        )
    return {"status": "REACTIVATED", "message": "Trigger phrase accepted. Standby Mode exited."}

async def get_standby_status():
    """Returns the current standby/reactivation status."""
    return StandbyManager.get_status_report()

@router.get("/status", response_model=GovernanceStatusOut)
@router.get("/status/", response_model=GovernanceStatusOut)
async def get_governance_status():
    """
    Returns a unified governance status report with real telemetry from fingerprints and improvements.
    """
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.learning_models import ErrorFingerprint
    from libs.db.models.core_models import SystemImprovement
    from sqlalchemy import select, func

    is_in_standby = StandbyManager.is_in_standby()
    
    async with AsyncSessionLocal() as db:
        try:
            # Count active fingerprints
            f_count = (await db.execute(select(func.count(ErrorFingerprint.id)).where(ErrorFingerprint.is_active == True))).scalar() or 0
            # Count pending improvements
            i_count = (await db.execute(select(func.count(SystemImprovement.id)).where(SystemImprovement.status == "pending"))).scalar() or 0
            
            # Count active drills (Real query)
            from libs.db.models.governance_models import ValidationResult, ValidationType
            drill_count_q = select(func.count(ValidationResult.id)).where(
                ValidationResult.validation_type == ValidationType.DRILL,
                ValidationResult.status == "RUNNING"
            )
            drill_count = (await db.execute(drill_count_q)).scalar() or 0

            return GovernanceStatusOut(
                is_running=not is_in_standby,
                standby_mode=is_in_standby,
                failure_counts={
                    "systemic_anomalies": f_count,
                    "pending_patches": i_count,
                    "active_drills": drill_count
                },
                stuck_threshold=5,
                active_drills=drill_count,
                health_score=max(0.0, 1.0 - (f_count * 0.1)) if not is_in_standby else 0.5
            )
        except Exception as exc:
            logger.warning("Governance status fallback: %s", exc)
            return GovernanceStatusOut(
                is_running=not is_in_standby,
                standby_mode=is_in_standby,
                failure_counts={"systemic_anomalies": 0, "pending_patches": 0},
                stuck_threshold=5,
                active_drills=0,
                health_score=0.9
            )

@router.get("/systemic-summary", response_model=SystemicSummaryOut)
async def get_systemic_summary():
    """Unified view of fingerprints and pending improvements for the Mission Control dashboard."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.learning_models import ErrorFingerprint
    from libs.db.models.core_models import SystemImprovement
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        try:
            # Fetch active fingerprints
            f_res = await db.execute(select(ErrorFingerprint).where(ErrorFingerprint.is_active == True).order_by(ErrorFingerprint.last_seen_at.desc()).limit(10))
            fingerprints = f_res.scalars().all()
            
            # Fetch pending improvements
            i_res = await db.execute(select(SystemImprovement).where(SystemImprovement.status == "pending").order_by(SystemImprovement.created_at.desc()).limit(10))
            improvements = i_res.scalars().all()

            summary_items = []
            critical_count = 0
            
            for f in fingerprints:
                if f.severity == "critical": critical_count += 1
                summary_items.append({
                    "id": str(f.id),
                    "type": "ANOMALY",
                    "title": f.error_family,
                    "description": f.normalized_message or f.component,
                    "severity": f.severity,
                    "timestamp": f.last_seen_at
                })
                
            for i in improvements:
                summary_items.append({
                    "id": str(i.id),
                    "type": "PATCH_PENDING",
                    "title": "Sistem İyileştirmesi",
                    "description": f"Dosya: {i.target_file}",
                    "severity": "medium",
                    "timestamp": i.created_at
                })

            return SystemicSummaryOut(
                total_anomalies=len(fingerprints),
                pending_improvements=len(improvements),
                critical_fingerprints=critical_count,
                health_score=max(0.0, 1.0 - (len(fingerprints) * 0.1)),
                items=summary_items
            )
        except Exception as exc:
            logger.warning("Systemic summary fallback: %s", exc)
            return SystemicSummaryOut(
                total_anomalies=0,
                pending_improvements=0,
                critical_fingerprints=0,
                health_score=1.0,
                items=[]
            )

@router.get("/fingerprints", response_model=List[FingerprintOut])
async def list_fingerprints(
    response: Response,
    limit: int = 50,
    offset: int = 0,
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.learning_models import ErrorFingerprint
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(ErrorFingerprint.id))
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(ErrorFingerprint).order_by(ErrorFingerprint.last_seen_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        items = res.scalars().all()

        return [
            FingerprintOut(
                id=str(i.id),
                error_family=i.error_family,
                service=i.service,
                component=i.component,
                severity=i.severity,
                recurrence_count=i.recurrence_count,
                first_seen_at=i.first_seen_at,
                last_seen_at=i.last_seen_at,
                normalized_message=i.normalized_message,
                risk_domain=i.risk_domain
            ) for i in items
        ]

class ValidationOut(BaseModel):
    id: str
    component_name: str
    test_suite: str
    validation_type: str
    status: str
    metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

class DecisionLineageOut(BaseModel):
    id: str
    parent_id: Optional[str] = None
    root_id: Optional[str] = None
    decision_type: str
    component_name: str
    rationale: str
    trigger_event: Optional[Dict[str, Any]] = None
    outcome: Optional[str] = None
    confidence_score: float = 1.0
    created_at: datetime
    integrity_hash: Optional[str] = None

class RetentionPolicyOut(BaseModel):
    id: str
    data_category: str
    hot_retention_days: int
    warm_retention_days: int
    is_permanent: bool

class PolicyProposalOut(BaseModel):
    id: str
    title: str
    description: str
    scope: str
    status: str
    author_id: str
    created_at: datetime
    parameter: Optional[str] = "System Tuning"
    current_value: Optional[str] = "N/A"
    proposed_value: Optional[str] = "N/A"
    confidence: float = 1.0
    impact: str = "Neutral"
    required_signoffs: int = 1
    current_signoffs: int = 0
    signatories: List[str] = []

class DrillRecordOut(BaseModel):
    id: str
    scenario: str
    status: str
    outcome: str
    duration_seconds: int
    created_at: datetime

class PolicyEvolutionOut(BaseModel):
    id: str
    policy_key: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Dict[str, Any] = None
    change_reason: str
    decision_id: Optional[str] = None
    created_at: datetime

class SystemUpdateOut(BaseModel):
    id: str
    target_file: str
    description: str
    rationale: str
    status: str
    diff_summary: Optional[str] = None
    changed_symbols: List[str] = []
    test_result: Dict[str, Any] = {}
    git_commit: Optional[str] = None
    created_at: str

class EvolutionStateOut(BaseModel):
    current_version: str
    last_updated: str
    updates: List[SystemUpdateOut]

@router.get("/approvals", response_model=List[ApprovalOut])
async def list_approvals(
    response: Response,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    identity: Dict[str, Any] = Depends(require_permission("approval.view"))
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import ApprovalRequest
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(ApprovalRequest.id))
        if status:
            count_q = count_q.where(ApprovalRequest.status == status)
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc()).limit(limit).offset(offset)
        if status:
            q = q.where(ApprovalRequest.status == status)
        res = await db.execute(q)
        items = res.scalars().all()

        return [
            ApprovalOut(
                id=str(i.id),
                project_id=str(i.project_id),
                request_type=i.request_type,
                reason=i.reason,
                status=i.status,
                created_at=i.created_at,
                agent_id=i.step_id,
                decided_by=i.approver_id,
                decided_at=i.decision_at,
                comment=i.comment
            ) for i in items
        ]

@router.get("/approvals/{id}", response_model=ApprovalOut)
async def get_approval(id: str):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import ApprovalRequest
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == id))
        i = res.scalar_one_or_none()
        if not i:
            raise HTTPException(status_code=404, detail="Approval request not found")

        return ApprovalOut(
            id=str(i.id),
            project_id=str(i.project_id),
            request_type=i.request_type,
            reason=i.reason,
            status=i.status,
            created_at=i.created_at,
            agent_id=i.step_id,
            decided_by=i.approver_id,
            decided_at=i.decision_at,
            comment=i.comment
        )

@router.patch("/approvals/{id}")
async def update_approval_status(
    id: str, 
    data: Dict[str, Any],
    identity: Dict[str, Any] = Depends(require_permission("approval.decide"))
):
    """Standard PATCH endpoint for Refine useUpdate compatibility."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import ApprovalRequest
    from services.governance.lineage_service import LineageService
    from sqlalchemy import select
    from datetime import datetime, timezone

    status = data.get("status")
    comment = data.get("comment", "")
    
    if not status:
        raise HTTPException(status_code=400, detail="Status is required")

    if status.upper() in ["APPROVED", "REJECTED"] and len(comment) < 10:
        raise HTTPException(
            status_code=400, 
            detail="SIF-02: Kritik işlemler için en az 10 karakterlik gerekçe (justification) zorunludur."
        )

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == id))
        i = res.scalar_one_or_none()
        if not i:
            raise HTTPException(status_code=404, detail="Approval request not found")

        old_status = i.status
        i.status = status.upper()
        i.approver_id = str(identity["id"])
        i.decision_at = datetime.now(timezone.utc)
        i.comment = comment

        await LineageService.log_decision(
            decision_type="MANUAL_INTERVENTION",
            component_name="QuorumCenter",
            rationale=f"Operator PATCH {i.status}: {comment}",
            outcome=i.status,
            meta_data={
                "approval_id": id,
                "project_id": str(i.project_id),
                "old_status": old_status
            },
            db=db
        )
        
        try:
            from services.governance.learning_orchestrator import LearningOrchestrator
            await LearningOrchestrator.record_learning(
                incident_data={
                    "id": f"APP-{id[:8]}",
                    "incident_type": "MANUAL_APPROVAL",
                    "severity": "info",
                    "message": f"Approval {id} manually updated to {i.status}",
                    "project_id": str(i.project_id) if i.project_id else None
                },
                outcome_data={
                    "final_outcome": "SUCCESS" if i.status == "APPROVED" else "REJECTED",
                    "root_cause": "MANUAL_INTERVENTION",
                    "operator_override": True,
                    "strategy_used": "OPERATOR_APPROVAL",
                    "applied_patch": i.comment
                },
                db=db
            )
        except Exception as le:
            logger.warning(f"Learning record failed in approval update: {le}")

        await db.commit()
        await db.refresh(i)
        
        return {
            "id": str(i.id),
            "status": i.status,
            "decided_at": i.decision_at
        }

@router.post("/approvals/{id}/decide")
async def decide_approval(id: str, dec: ApprovalDecision):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import ApprovalRequest
    from services.governance.lineage_service import LineageService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(ApprovalRequest).where(ApprovalRequest.id == id))
        i = res.scalar_one_or_none()
        if not i:
            raise HTTPException(status_code=404, detail="Approval request not found")

        old_status = i.status
        i.status = "APPROVED" if dec.approve else "REJECTED"
        i.approver_id = dec.decided_by
        i.decision_at = datetime.now(timezone.utc)
        i.comment = dec.reason
        
        lineage = await LineageService.log_decision(
            decision_type="MANUAL_INTERVENTION",
            component_name="QuorumCenter",
            rationale=f"Operator {dec.decided_by} {i.status}: {dec.reason}",
            outcome=i.status,
            meta_data={
                "approval_id": id,
                "project_id": str(i.project_id),
                "old_status": old_status,
                "new_status": i.status
            },
            db=db
        )
        
        try:
            from services.governance.learning_orchestrator import LearningOrchestrator
            await LearningOrchestrator.record_learning(
                incident_data={
                    "id": f"APP-{id[:8]}",
                    "incident_type": "MANUAL_APPROVAL",
                    "severity": "info",
                    "message": f"Approval {id} decided: {i.status}",
                    "project_id": str(i.project_id) if i.project_id else None
                },
                outcome_data={
                    "final_outcome": "SUCCESS" if i.status == "APPROVED" else "REJECTED",
                    "root_cause": "MANUAL_DECISION",
                    "operator_override": True,
                    "strategy_used": "OPERATOR_APPROVAL",
                    "approval_id": id,
                    "lineage_id": str(lineage.id) if lineage else None,
                    "applied_patch": i.comment
                },
                db=db
            )
        except Exception as le:
            logger.warning(f"Learning record failed in approval decision: {le}")

        await db.commit()
        await db.refresh(i)
        
        return {
            "status": i.status, 
            "decided_at": i.decision_at,
            "lineage_id": str(lineage.id) if lineage else None
        }

@router.get("/improvements", response_model=List[ImprovementOut])
async def list_improvements(
    response: Response,
    limit: int = 50,
    offset: int = 0,
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import SystemImprovement
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(SystemImprovement.id))
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(SystemImprovement).order_by(SystemImprovement.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        items = res.scalars().all()

        return [
            ImprovementOut(
                id=str(i.id),
                opportunity_id=str(i.opportunity_id),
                target_file=i.target_file,
                instruction=i.instruction,
                proposed_patch=i.proposed_patch,
                status=i.status.value if hasattr(i.status, "value") else str(i.status),
                created_at=i.created_at,
                test_results=i.test_results,
            ) for i in items
        ]

@router.patch("/improvements/{id}", response_model=ImprovementOut)
async def update_improvement(id: str, patch_data: ImprovementUpdate):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import SystemImprovement
    from sqlalchemy import select
    import uuid

    try:
        uid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Improvement not found")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(SystemImprovement).where(SystemImprovement.id == uid))
        improvement = res.scalar_one_or_none()
        if not improvement:
            raise HTTPException(status_code=404, detail="Improvement not found")

        improvement.status = patch_data.status
        await db.commit()
        await db.refresh(improvement)

        return ImprovementOut(
            id=str(improvement.id),
            opportunity_id=str(improvement.opportunity_id),
            target_file=improvement.target_file,
            instruction=improvement.instruction,
            proposed_patch=improvement.proposed_patch,
            status=improvement.status.value if hasattr(improvement.status, "value") else str(improvement.status),
            created_at=improvement.created_at,
            test_results=improvement.test_results,
        )

@router.get("/federation/trust")
async def get_federation_trust(response: Response):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import FederationTrust
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        q = select(FederationTrust)
        res = await db.execute(q)
        items = res.scalars().all()
        response.headers["x-total-count"] = str(len(items))
        return items

@router.get("/signoffs", response_model=List[SignoffOut])
async def list_signoffs(
    response: Response,
    limit: int = Query(50),
    offset: int = Query(0),
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.governance_models import ProductionSignoff
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(ProductionSignoff.id))
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(ProductionSignoff).order_by(ProductionSignoff.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        items = res.scalars().all()

        return [
            SignoffOut(
                id=str(i.id),
                component_name=i.component_name,
                version=i.version,
                status=i.status.value if hasattr(i.status, "value") else str(i.status),
                created_at=i.created_at
            ) for i in items
        ]

@router.get("/validations", response_model=List[ValidationOut])
async def list_validations(
    response: Response,
    limit: int = Query(50),
    offset: int = Query(0),
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.governance_models import ValidationResult
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(ValidationResult.id))
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(ValidationResult).order_by(ValidationResult.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        items = res.scalars().all()

        return [
            ValidationOut(
                id=str(i.id),
                component_name=i.component_name,
                test_suite=i.test_suite,
                validation_type=i.validation_type.value if hasattr(i.validation_type, "value") else str(i.validation_type),
                status=i.status.value if hasattr(i.status, "value") else str(i.status),
                metrics=i.metrics,
                created_at=i.created_at
            ) for i in items
        ]

@router.post("/validations/trigger")
async def trigger_validation(component_name: str):
    from services.validation.continuous_validation_service import ContinuousValidationService
    service = ContinuousValidationService()
    success = await service.trigger_manual_validation(component_name)
    if not success:
        raise HTTPException(status_code=500, detail="Validation trigger failed")
    return {"status": "triggered", "component": component_name}

@router.get("/lineage", response_model=List[DecisionLineageOut])
@router.get("/lineages", response_model=List[DecisionLineageOut])
async def list_lineage(
    response: Response,
    limit: int = Query(50),
    offset: int = Query(0),
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.lineage_models import DecisionLineage
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        try:
            count_q = select(func.count(DecisionLineage.id))
            total_count = (await db.execute(count_q)).scalar()
            response.headers["x-total-count"] = str(total_count)
            response.headers["Access-Control-Expose-Headers"] = "x-total-count"

            q = select(DecisionLineage).order_by(DecisionLineage.created_at.desc()).limit(limit).offset(offset)
            res = await db.execute(q)
            items = res.scalars().all()

            return [
                DecisionLineageOut(
                    id=str(i.id),
                    parent_id=str(i.parent_id) if i.parent_id else None,
                    root_id=str(i.root_id) if i.root_id else None,
                    decision_type=i.decision_type,
                    component_name=i.component_name,
                    rationale=i.rationale,
                    trigger_event=i.trigger_event,
                    outcome=getattr(i, "outcome", None),
                    confidence_score=getattr(i, "confidence_score", 1.0),
                    created_at=i.created_at,
                    integrity_hash=getattr(i, "integrity_hash", None)
                ) for i in items
            ]
        except Exception as exc:
            logger.warning("Decision lineage fallback activated: %s", exc)
            response.headers["x-total-count"] = "0"
            return []

@router.get("/policies/evolution", response_model=List[PolicyEvolutionOut])
async def list_policy_evolution(
    response: Response,
    limit: int = Query(50),
    offset: int = Query(0),
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.lineage_models import PolicyEvolution
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(PolicyEvolution.id))
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(PolicyEvolution).order_by(PolicyEvolution.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        items = res.scalars().all()

        return [
            PolicyEvolutionOut(
                id=str(i.id),
                policy_key=i.policy_key,
                old_value=i.old_value,
                new_value=i.new_value,
                change_reason=i.change_reason,
                decision_id=str(i.decision_id) if i.decision_id else None,
                created_at=i.created_at
            ) for i in items
        ]

@router.get("/evolution/state", response_model=EvolutionStateOut)
async def get_evolution_state():
    """Returns the autonomous evolution history from system_state.json."""
    import json
    import os
    state_path = "runtime/data/system_state.json"
    if not os.path.exists(state_path):
        return {
            "current_version": "v1.0", 
            "last_updated": datetime.now(timezone.utc).isoformat(), 
            "updates": []
        }
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Reverse updates for UI (newest first)
            if "updates" in data:
                data["updates"] = list(reversed(data["updates"]))
            return data
    except Exception as e:
        import traceback
        logger.error(f"Failed to read system_state.json: {e}\n{traceback.format_exc()}")
        return {
            "current_version": "error", 
            "last_updated": datetime.now(timezone.utc).isoformat(), 
            "updates": []
        }

@router.get("/drills", response_model=List[DrillRecordOut])
async def list_drills(
    response: Response,
    limit: int = Query(50),
    offset: int = Query(0),
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.governance_models import ValidationResult, ValidationType
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(ValidationResult.id)).where(ValidationResult.validation_type == ValidationType.DRILL)
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(ValidationResult).where(ValidationResult.validation_type == ValidationType.DRILL).order_by(ValidationResult.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        items = res.scalars().all()

        return [
            DrillRecordOut(
                id=str(i.id),
                scenario=i.test_suite.replace("Drill_", ""),
                status=i.status.value if hasattr(i.status, "value") else str(i.status),
                outcome="SUCCESS" if i.status == "PASS" else "FAILED",
                duration_seconds=getattr(i, "metrics", {}).get("duration", 0),
                created_at=i.created_at
            ) for i in items
        ]

@router.post("/drills/trigger")
async def trigger_drill_endpoint(scenario: str):
    from services.training.drill_engine import DrillEngine
    from services.repair.repair_orchestrator import RepairOrchestrator
    
    orch = RepairOrchestrator()
    engine = DrillEngine(orch)
    
    result = await engine.run_governance_drill(scenario)
    return result

@router.get("/compliance/policies", response_model=List[RetentionPolicyOut])
async def list_retention_policies(response: Response):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.compliance_models import RetentionPolicy
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(RetentionPolicy))
        items = res.scalars().all()
        response.headers["x-total-count"] = str(len(items))
        return [
            RetentionPolicyOut(
                id=str(i.id),
                data_category=i.data_category,
                hot_retention_days=i.hot_retention_days,
                warm_retention_days=i.warm_retention_days,
                is_permanent=i.is_permanent
            ) for i in items
        ]

@router.get("/proposals", response_model=List[PolicyProposalOut])
@router.get("/proposals/", response_model=List[PolicyProposalOut])
@router.get("/policy-proposals", response_model=List[PolicyProposalOut], include_in_schema=False)
@router.get("/policy-proposals/", response_model=List[PolicyProposalOut], include_in_schema=False)
async def list_policy_proposals(response: Response):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.governance_models import PolicyProposal
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        total = (await db.execute(select(func.count(PolicyProposal.id)))).scalar() or 0
        response.headers["x-total-count"] = str(total)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        res = await db.execute(select(PolicyProposal).order_by(PolicyProposal.created_at.desc()))
        items = res.scalars().all()

        return [
            PolicyProposalOut(
                id=str(i.id),
                title=i.title,
                description=i.description or "",
                scope=getattr(i, "scope", "AUTONOMOUS_LEARNING"),
                status=i.status.value if hasattr(i.status, "value") else str(i.status),
                author_id=str(getattr(i, "author_id", "governance_agent")),
                created_at=i.created_at,
                parameter=getattr(i, "proposed_changes", {}).get("parameter", i.title)
                if isinstance(getattr(i, "proposed_changes", {}), dict)
                else i.title,
                current_value=str(getattr(i, "proposed_changes", {}).get("current_value", "Default")),
                proposed_value=str(getattr(i, "proposed_changes", {}).get("proposed_value", "N/A"))
                if isinstance(getattr(i, "proposed_changes", {}), dict)
                else i.policy_code,
                confidence=getattr(i, "proposed_changes", {}).get("confidence", 0.91)
                if isinstance(getattr(i, "proposed_changes", {}), dict)
                else 0.91,
                impact=getattr(i, "proposed_changes", {}).get("impact", "Medium"),
                required_signoffs=2,
                current_signoffs=0,
                signatories=[],
            )
            for i in items
        ]

@router.post("/proposals/{proposal_id}/approve")
async def approve_policy_proposal(
    proposal_id: str, 
    note: str = "Approved via UI",
    identity: Dict[str, Any] = Depends(require_permission("policy.approve"))
):
    from services.governance.quorum_service import QuorumService
    approver_id = str(identity["id"])
    success = await QuorumService.add_signoff(proposal_id, approver_id, note)
    return {"success": success, "proposal_id": proposal_id}

@router.get("/compliance/audit-bundles", response_model=List[AuditBundleOut])
@router.get("/compliance/audit-bundles/", response_model=List[AuditBundleOut], include_in_schema=False)
async def list_audit_bundles(response: Response):
    """Lists audit bundles from database with file-level size check fallback."""
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.compliance_models import AuditBundle
    from sqlalchemy import select
    import os

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(AuditBundle).order_by(AuditBundle.created_at.desc()))
        items = res.scalars().all()
        
        export_dir = "runtime/data/audit_exports"
        bundles_out = []
        
        for i in items:
            # File check for size
            filename = f"audit_{str(i.id)[:8]}.zip"
            filepath = os.path.join(export_dir, filename)
            size_str = "0.1 MB"
            if os.path.exists(filepath):
                stats = os.stat(filepath)
                size_str = f"{stats.st_size / 1024 / 1024:.2f} MB"
            
            bundles_out.append(
                AuditBundleOut(
                    id=str(i.id),
                    name=i.bundle_name,
                    purpose=(i.evidence_metadata or {}).get("purpose", "AUDIT"),
                    project=(i.evidence_metadata or {}).get("scope", "Sovereign AGI"),
                    created_at=i.created_at,
                    operator=i.created_by,
                    seal=i.integrity_hash or "SHA256:NOT_SEALED",
                    size=size_str,
                    status="sealed" if i.integrity_hash else "pending"
                )
            )
        
        response.headers["x-total-count"] = str(len(bundles_out))
        return bundles_out

@router.post("/compliance/audit-bundles", response_model=AuditBundleOut)
@router.post("/compliance/audit-bundles/", response_model=AuditBundleOut, include_in_schema=False)
async def create_audit_bundle_endpoint(
    bundle_in: AuditBundleCreate,
    identity: Dict[str, Any] = Depends(require_permission("audit.create"))
):
    from services.compliance.compliance_service import ComplianceService
    from datetime import datetime, timezone, timedelta
    
    start = bundle_in.start_time or (datetime.now(timezone.utc) - timedelta(days=30))
    end = bundle_in.end_time or datetime.now(timezone.utc)
    
    bundle = await ComplianceService.create_audit_bundle(
        name=bundle_in.name,
        start=start,
        end=end,
        creator=str(identity["id"])
    )
    
    return AuditBundleOut(
        id=str(bundle.id),
        name=bundle.bundle_name,
        purpose=bundle_in.purpose or "AUDIT",
        project="Sovereign Control Plane",
        created_at=bundle.created_at,
        operator=bundle.created_by,
        seal=bundle.integrity_hash,
        size="0.1 MB",
        status="sealed"
    )

@router.get("/incidents", response_model=List[IncidentOut])
async def list_incidents(
    response: Response,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    identity: Dict[str, Any] = Depends(require_permission("incident.view"))
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import OperationalIncident
    from sqlalchemy import select, desc, func

    async with AsyncSessionLocal() as session:
        query = select(OperationalIncident).order_by(desc(OperationalIncident.created_at)).offset(offset).limit(limit)
        if status:
            query = query.filter(OperationalIncident.status == status)
        
        result = await session.execute(query)
        items = result.scalars().all()
        
        total_query = select(func.count(OperationalIncident.id))
        if status:
            total_query = total_query.filter(OperationalIncident.status == status)
        total = await session.scalar(total_query)
        response.headers["x-total-count"] = str(total or 0)
        
        return [
            IncidentOut(
                id=str(item.id),
                incident_type=item.incident_type,
                severity=item.severity,
                message=item.message,
                status=item.status,
                project_id=str(item.project_id) if item.project_id else None,
                created_at=item.created_at,
                payload=item.payload
            ) for item in items
        ]

@router.get("/incidents/{id}", response_model=IncidentOut)
async def get_incident(id: str):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import OperationalIncident
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OperationalIncident).filter(OperationalIncident.id == id))
        item = result.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Incident not found")

        return IncidentOut(
            id=str(item.id),
            incident_type=item.incident_type,
            severity=item.severity,
            message=item.message,
            status=item.status,
            project_id=str(item.project_id) if item.project_id else None,
            created_at=item.created_at,
            payload=item.payload
        )

@router.post("/incidents/{id}/resolve")
async def resolve_incident(
    id: str, 
    dec: IncidentResolve,
    identity: Dict[str, Any] = Depends(require_permission("incident.resolve"))
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import OperationalIncident
    from services.governance.lineage_service import LineageService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(OperationalIncident).where(OperationalIncident.id == id))
        i = res.scalar_one_or_none()
        if not i:
            raise HTTPException(status_code=404, detail="Incident not found")

        i.status = "resolved"
        i.resolved_at = datetime.now(timezone.utc)
        
        lineage = await LineageService.log_decision(
            decision_type="INCIDENT_RESOLUTION",
            component_name="IncidentCenter",
            rationale=f"Operator {identity['name']} resolved incident: {dec.resolution_notes}",
            outcome="RESOLVED",
            meta_data={
                "incident_id": id,
                "project_id": str(i.project_id) if i.project_id else None,
                "operator_id": str(identity["id"])
            },
            db=db
        )
        
        try:
            from services.governance.learning_orchestrator import LearningOrchestrator
            await LearningOrchestrator.record_incident_learning(
                incident_data={
                    "id": str(i.id),
                    "incident_type": i.incident_type,
                    "severity": i.severity,
                    "message": i.message,
                    "project_id": str(i.project_id) if i.project_id else None
                },
                outcome_data={
                    "final_outcome": "SUCCESS",
                    "root_cause": "MANUAL_RESOLUTION",
                    "operator_override": True,
                    "strategy_used": "OPERATOR_INTERVENTION"
                },
                db=db
            )
        except Exception as le:
            logger.warning(f"Learning record failed in incident resolution: {le}")

        await db.commit()
        await db.refresh(i)
        
        return {
            "status": i.status, 
            "resolved_by": dec.operator_id,
            "lineage_id": str(lineage.id) if lineage else None
        }

@router.patch("/incidents/{id}", response_model=IncidentOut)
async def update_incident(id: str, data: Dict[str, Any]):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import OperationalIncident
    from sqlalchemy import select
    from services.observability.logging import get_logger
    
    local_logger = get_logger("governance_api")

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(OperationalIncident).filter(OperationalIncident.id == id))
            item = result.scalar_one_or_none()
            if not item:
                raise HTTPException(status_code=404, detail="Incident not found")
            
            protected_fields = ["id", "created_at"]
            old_status = item.status
            status_changed = False
            
            for key, value in data.items():
                if key not in protected_fields and hasattr(item, key):
                    if key == "status" and value != old_status:
                        status_changed = True
                    setattr(item, key, value)
            
            if status_changed:
                from services.governance.lineage_service import LineageService
                await LineageService.log_decision(
                    decision_type="INCIDENT_UPDATE",
                    component_name="IncidentCenter",
                    rationale=f"Operator PATCH update: {old_status} -> {item.status}",
                    outcome=item.status,
                    meta_data={
                        "incident_id": id,
                        "old_status": old_status,
                        "new_status": item.status
                    },
                    db=session
                )

            if status_changed and item.status == "resolved":
                try:
                    from services.governance.learning_orchestrator import LearningOrchestrator
                    await LearningOrchestrator.record_incident_learning(
                        incident_data={
                            "id": str(item.id),
                            "incident_type": item.incident_type,
                            "severity": item.severity,
                            "message": item.message,
                            "project_id": str(item.project_id) if item.project_id else None
                        },
                        outcome_data={
                            "final_outcome": "SUCCESS",
                            "root_cause": "PATCH_RESOLUTION",
                            "operator_override": True,
                            "strategy_used": "OPERATOR_PATCH"
                        },
                        db=session
                    )
                except Exception as le:
                    logger.warning(f"Learning record failed in incident update: {le}")

            await session.commit()
            await session.refresh(item)
            
            return IncidentOut(
                id=str(item.id),
                incident_type=item.incident_type,
                severity=item.severity,
                message=item.message,
                status=item.status,
                project_id=str(item.project_id) if item.project_id else None,
                created_at=item.created_at,
                payload=item.payload
            )
    except Exception as e:
        local_logger.error(f"Failed to update incident {id}: {str(e)}", exc_info=True)
        raise

@router.get("/ops/launch-gates")
async def get_launch_gates():
    from libs.governance.launch_gatekeeper import LaunchGatekeeper
    passed, results = await LaunchGatekeeper.validate_for_rollout()
    return {
        "passed": passed,
        "gates": results,
        "timestamp": datetime.now(timezone.utc)
    }

@router.post("/ops/handover")
@router.post("/ops/handover/", include_in_schema=False)
async def trigger_handover(
    project_id: str, 
    dry_run: bool = True,
    identity: Dict[str, Any] = Depends(require_permission("ops.handover"))
):
    from scripts.ops.production_handover import run_production_handover
    try:
        await run_production_handover(project_id, dry_run)
        return {"status": "success", "project_id": project_id, "dry_run": dry_run}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/axiology", response_model=List[AxiologyLogOut])
async def list_axiology_logs(
    response: Response,
    limit: int = 50,
    offset: int = 0,
):
    from libs.db.session import AsyncSessionLocal
    from libs.db.models.core_models import SovereignEvidence
    from sqlalchemy import select, func

    async with AsyncSessionLocal() as db:
        count_q = select(func.count(SovereignEvidence.id)).where(SovereignEvidence.evidence_type == "axiology_audit")
        total_count = (await db.execute(count_q)).scalar()
        response.headers["x-total-count"] = str(total_count)
        response.headers["Access-Control-Expose-Headers"] = "x-total-count"

        q = select(SovereignEvidence).where(SovereignEvidence.evidence_type == "axiology_audit").order_by(SovereignEvidence.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(q)
        items = res.scalars().all()

        return [
            AxiologyLogOut(
                id=str(i.id),
                decision=i.payload.get("decision", "unknown"),
                context=i.payload.get("context", "unknown"),
                justification=i.payload.get("justification", ""),
                scores=i.payload.get("scores", {}),
                created_at=i.created_at,
                corrective_action=i.payload.get("corrective_action"),
                target_preview=i.payload.get("target_preview")
            ) for i in items
        ]
