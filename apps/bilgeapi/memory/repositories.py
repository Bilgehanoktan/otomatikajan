from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc
from apps.bilgeapi.memory.models import (
    SystemModel, TaskModel, EventLogModel, AuditLogModel,
    DecisionModel, ApprovalModel, QuarantineItemModel
)

def _to_dict(model_obj) -> Optional[Dict[str, Any]]:
    if not model_obj:
        return None
    res = {}
    for col in model_obj.__table__.columns:
        val = getattr(model_obj, col.name)
        if isinstance(val, datetime):
            res[col.name] = val.isoformat()
        else:
            res[col.name] = val
    return res

async def _log_security_event(session: AsyncSession, event_type: str, actor_id: str, action: str, target: str, tenant_id: str, actual_tenant: str):
    audit = AuditLogModel(
        event_type=event_type,
        actor_id=actor_id,
        actor_type="system",
        action=action,
        target=target,
        status="DENIED",
        risk_level="HIGH",
        tenant_id=tenant_id,
        before_state={"requested_tenant": tenant_id},
        after_state={"actual_tenant": actual_tenant}
    )
    session.add(audit)
    await session.flush()

class SystemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update(
        self,
        system_name: str,
        project_type: str,
        root_path: str,
        health_score: float,
        metadata_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        stmt = select(SystemModel).where(SystemModel.root_path == root_path)
        res = await self.session.execute(stmt)
        system = res.scalar_one_or_none()

        if system:
            system.system_name = system_name
            system.project_type = project_type
            system.health_score = health_score
            system.metadata_fields = metadata_fields or {}
            system.scanned_at = datetime.utcnow()
        else:
            system = SystemModel(
                system_name=system_name,
                project_type=project_type,
                root_path=root_path,
                health_score=health_score,
                metadata_fields=metadata_fields or {}
            )
            self.session.add(system)
        
        await self.session.flush()
        return _to_dict(system)

    async def get_by_root(self, root_path: str) -> Optional[Dict[str, Any]]:
        stmt = select(SystemModel).where(SystemModel.root_path == root_path)
        res = await self.session.execute(stmt)
        return _to_dict(res.scalar_one_or_none())


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        tenant_id: str = "default",
        system_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        agent_role: Optional[str] = None,
        action_type: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        task = TaskModel(
            tenant_id=tenant_id,
            system_id=system_id,
            title=title,
            description=description,
            agent_role=agent_role,
            action_type=action_type,
            status=status or "PENDING",
            risk_level=risk_level or "LOW",
            payload=payload or {},
            max_attempts=max_attempts
        )
        self.session.add(task)
        await self.session.flush()
        return _to_dict(task)

    async def get_task(self, tenant_id: str = "default", task_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if task_id is None:
            task_id = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        res = await self.session.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            return None
        if task.tenant_id != tenant_id:
            await _log_security_event(
                self.session,
                event_type="CROSS_TENANT_ACCESS_DENIED",
                actor_id="anonymous",
                action="get_task",
                target=f"task:{task_id}",
                tenant_id=tenant_id,
                actual_tenant=task.tenant_id
            )
            return None
        return _to_dict(task)

    async def update_task_status(
        self,
        tenant_id: str = "default",
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        attempt_increment: bool = False
    ) -> Optional[Dict[str, Any]]:
        if status is None or isinstance(status, bool):
            actual_attempt_increment = status if isinstance(status, bool) else attempt_increment
            status = task_id
            task_id = tenant_id
            tenant_id = "default"
            attempt_increment = actual_attempt_increment
        if not tenant_id:
            tenant_id = "default"
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        res = await self.session.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            return None
        if task.tenant_id != tenant_id:
            await _log_security_event(
                self.session,
                event_type="CROSS_TENANT_ACCESS_DENIED",
                actor_id="anonymous",
                action="update_task_status",
                target=f"task:{task_id}",
                tenant_id=tenant_id,
                actual_tenant=task.tenant_id
            )
            return None
        
        task.status = status
        if attempt_increment:
            task.attempt_count += 1
        task.updated_at = datetime.utcnow()
        await self.session.flush()
        return _to_dict(task)

    async def list_tasks(self, tenant_id: str = "default", system_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if system_id is None:
            system_id = tenant_id
            tenant_id = "default"
        elif system_id in {"PENDING", "RUNNING", "COMPLETED", "FAILED", "BLOCKED", "PENDING_APPROVED", "DENIED"}:
            status = system_id
            system_id = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        stmt = select(TaskModel).where(TaskModel.system_id == system_id, TaskModel.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(TaskModel.status == status)
        stmt = stmt.order_by(TaskModel.created_at.desc())
        res = await self.session.execute(stmt)
        return [_to_dict(t) for t in res.scalars().all()]


class EventLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_event(self, system_id: str, event_type: str, message: str) -> Dict[str, Any]:
        event = EventLogModel(
            system_id=system_id,
            event_type=event_type,
            message=message
        )
        self.session.add(event)
        await self.session.flush()
        return _to_dict(event)

    async def list_events(self, system_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        stmt = select(EventLogModel).where(EventLogModel.system_id == system_id).order_by(EventLogModel.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return [_to_dict(e) for e in res.scalars().all()]


class AuditLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_audit(
        self,
        tenant_id: str = "default",
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_type: Optional[str] = None,
        action: Optional[str] = None,
        target: Optional[str] = None,
        status: Optional[str] = None,
        risk_level: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        audit = AuditLogModel(
            tenant_id=tenant_id,
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            target=target,
            status=status,
            risk_level=risk_level,
            before_state=before_state or {},
            after_state=after_state or {}
        )
        self.session.add(audit)
        await self.session.flush()
        return _to_dict(audit)

    async def list_recent_audits(self, tenant_id: str = "default", limit: int = 100) -> List[Dict[str, Any]]:
        if isinstance(tenant_id, int):
            limit = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        stmt = select(AuditLogModel).where(AuditLogModel.tenant_id == tenant_id).order_by(AuditLogModel.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return [_to_dict(a) for a in res.scalars().all()]


class DecisionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_decision(
        self,
        tenant_id: str = "default",
        task_id: Optional[str] = None,
        classification: Optional[str] = None,
        risk_score: Optional[float] = None,
        risk_level: Optional[str] = None,
        eligibility: Optional[str] = None,
        requires_human_gate: bool = False,
        decision_reason: Optional[str] = None,
        reasons: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        decision = DecisionModel(
            tenant_id=tenant_id,
            task_id=task_id,
            classification=classification,
            risk_score=risk_score if risk_score is not None else 0.0,
            risk_level=risk_level or "LOW",
            eligibility=eligibility or "ELIGIBLE",
            requires_human_gate=requires_human_gate,
            decision_reason=decision_reason or "",
            reasons=reasons or []
        )
        self.session.add(decision)
        await self.session.flush()
        return _to_dict(decision)

    async def get_decision_by_task(self, tenant_id: str = "default", task_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if task_id is None:
            task_id = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        stmt = select(DecisionModel).where(DecisionModel.task_id == task_id)
        res = await self.session.execute(stmt)
        decision = res.scalars().first()
        if not decision:
            return None
        if decision.tenant_id != tenant_id:
            await _log_security_event(
                self.session,
                event_type="CROSS_TENANT_ACCESS_DENIED",
                actor_id="anonymous",
                action="get_decision_by_task",
                target=f"decision_task:{task_id}",
                tenant_id=tenant_id,
                actual_tenant=decision.tenant_id
            )
            return None
        return _to_dict(decision)


class ApprovalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def request_approval(
        self,
        tenant_id: str = "default",
        task_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        request_type: Optional[str] = None,
        token: Optional[str] = None,
        action_hash: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if request_type is None:
            request_type = decision_id
            decision_id = task_id
            task_id = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        approval = ApprovalModel(
            tenant_id=tenant_id,
            task_id=task_id,
            decision_id=decision_id,
            request_type=request_type,
            status="PENDING",
            token=token,
            action_hash=action_hash,
            expires_at=expires_at
        )
        self.session.add(approval)
        await self.session.flush()
        return _to_dict(approval)

    async def submit_approval(
        self,
        tenant_id: str = "default",
        approval_id: Optional[str] = None,
        status: Optional[str] = None,
        reason: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        if approved_by is None:
            approved_by = reason
            reason = status
            status = approval_id
            approval_id = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        stmt = select(ApprovalModel).where(ApprovalModel.id == approval_id)
        res = await self.session.execute(stmt)
        approval = res.scalar_one_or_none()
        if not approval:
            return None
        if approval.tenant_id != tenant_id:
            await _log_security_event(
                self.session,
                event_type="CROSS_TENANT_ACCESS_DENIED",
                actor_id="anonymous",
                action="submit_approval",
                target=f"approval:{approval_id}",
                tenant_id=tenant_id,
                actual_tenant=approval.tenant_id
            )
            return None
        approval.status = status
        approval.reason = reason
        approval.approved_by = approved_by
        approval.approved_at = datetime.utcnow()
        await self.session.flush()
        return _to_dict(approval)

    async def get_pending_approvals(self, tenant_id: str = "default") -> List[Dict[str, Any]]:
        if not tenant_id:
            tenant_id = "default"
        stmt = select(ApprovalModel).where(ApprovalModel.status == "PENDING", ApprovalModel.tenant_id == tenant_id).order_by(ApprovalModel.created_at.desc())
        res = await self.session.execute(stmt)
        return [_to_dict(a) for a in res.scalars().all()]


class QuarantineItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def quarantine_file(
        self,
        tenant_id: str = "default",
        filepath: Optional[str] = None,
        original_hash: Optional[str] = None,
        quarantine_path: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = "default"
        item = QuarantineItemModel(
            tenant_id=tenant_id,
            filepath=filepath,
            original_hash=original_hash,
            quarantine_path=quarantine_path,
            reason=reason,
            restored=False
        )
        self.session.add(item)
        await self.session.flush()
        return _to_dict(item)

    async def restore_file(self, tenant_id: str = "default", item_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if item_id is None:
            item_id = tenant_id
            tenant_id = "default"
        if not tenant_id:
            tenant_id = "default"
        stmt = select(QuarantineItemModel).where(QuarantineItemModel.id == item_id)
        res = await self.session.execute(stmt)
        item = res.scalar_one_or_none()
        if not item:
            return None
        if item.tenant_id != tenant_id:
            await _log_security_event(
                self.session,
                event_type="CROSS_TENANT_ACCESS_DENIED",
                actor_id="anonymous",
                action="restore_file",
                target=f"quarantine:{item_id}",
                tenant_id=tenant_id,
                actual_tenant=item.tenant_id
            )
            return None
        item.restored = True
        await self.session.flush()
        return _to_dict(item)
