import os
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from apps.bilgeapi.memory.repositories import (
    ApprovalRepository, TaskRepository, DecisionRepository, AuditLogRepository
)

logger = logging.getLogger("bilgeapi.governance.approval_engine")

class ApprovalEngine:
    @staticmethod
    async def create_approval_request(
        task_id: str,
        decision_id: str,
        request_type: str,
        action_hash: str,
        tenant_id: str = "default",
        session: Optional[AsyncSession] = None,
        expiration_minutes: int = 15
    ) -> Dict[str, Any]:
        if not isinstance(tenant_id, str):
            session = tenant_id
            tenant_id = "default"
        """
        Creates a new approval request in the database with a secure one-time token
        and an expiration timestamp.
        """
        app_repo = ApprovalRepository(session)
        
        # Generate a secure one-time token
        token = secrets.token_hex(32)
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
        
        # Create approval record
        approval = await app_repo.request_approval(
            tenant_id=tenant_id,
            task_id=task_id,
            decision_id=decision_id,
            request_type=request_type,
            token=token,
            action_hash=action_hash,
            expires_at=expires_at
        )
        
        logger.info(f"Created approval request {approval['id']} for task {task_id}")
        return approval

    @staticmethod
    async def validate_and_submit_approval(
        approval_id: str,
        token: str,
        status: str,  # APPROVED or REJECTED
        chat_id: str,
        action_hash: str,
        approved_by: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Validates the incoming approval request parameters and records the decision.
        """
        app_repo = ApprovalRepository(session)
        task_repo = TaskRepository(session)
        dec_repo = DecisionRepository(session)
        audit_repo = AuditLogRepository(session)

        # 1. Chat ID check
        allowed_chat_id = os.getenv("BILGEAPI_TELEGRAM_CHAT_ID", "")
        allowed_ids = [cid.strip() for cid in allowed_chat_id.split(",") if cid.strip()]
        if not allowed_ids or str(chat_id) not in allowed_ids:
            # Audit unauthorized attempt
            await audit_repo.log_audit(
                "default",
                event_type="UNAUTHORIZED_APPROVAL_ATTEMPT",
                actor_id=str(chat_id),
                actor_type="UNKNOWN",
                action="SUBMIT",
                target=f"approval:{approval_id}",
                status="DENIED",
                risk_level="CRITICAL",
                before_state={"chat_id": chat_id},
                after_state=None
            )
            await session.commit()
            raise ValueError("Unauthorized chat_id")

        # 2. SQLite approval_id match
        # Fetch approval record. If missing, raise ValueError.
        from sqlalchemy import select
        from apps.bilgeapi.memory.models import ApprovalModel
        stmt = select(ApprovalModel).where(ApprovalModel.id == approval_id)
        res = await session.execute(stmt)
        db_approval = res.scalar_one_or_none()
        
        if not db_approval:
            # Audit missing approval ID
            await audit_repo.log_audit(
                "default",
                event_type="APPROVAL_NOT_FOUND",
                actor_id=approved_by,
                actor_type="HUMAN",
                action="SUBMIT",
                target=f"approval:{approval_id}",
                status="DENIED",
                risk_level="MEDIUM",
                before_state={"approval_id": approval_id},
                after_state=None
            )
            await session.commit()
            raise ValueError("Missing approval_id")

        tenant_id = db_approval.tenant_id or "default"

        approval_record = {
            "id": db_approval.id,
            "tenant_id": db_approval.tenant_id,
            "task_id": db_approval.task_id,
            "decision_id": db_approval.decision_id,
            "request_type": db_approval.request_type,
            "status": db_approval.status,
            "token": db_approval.token,
            "action_hash": db_approval.action_hash,
            "expires_at": db_approval.expires_at,
            "approved_by": db_approval.approved_by,
            "approved_at": db_approval.approved_at
        }

        task_id = approval_record["task_id"]
        
        # Load task and original decision to get risk levels for audit logging
        task = await task_repo.get_task(tenant_id, task_id)
        risk_level = task["risk_level"] if task else "HIGH"
        risk_score = 7.0
        orig_dec = await dec_repo.get_decision_by_task(tenant_id, task_id)
        if orig_dec:
            risk_score = orig_dec["risk_score"]
            risk_level = orig_dec["risk_level"]

        # Helper to log audit/decision failure
        async def log_failure(reason_msg: str, status_code: str = "DENIED"):
            await audit_repo.log_audit(
                tenant_id,
                event_type="APPROVAL_VALIDATION_FAILED",
                actor_id=approved_by,
                actor_type="HUMAN",
                action="SUBMIT",
                target=f"approval:{approval_id}",
                status=status_code,
                risk_level=risk_level,
                before_state={"approval_id": approval_id, "reason": reason_msg},
                after_state=None
            )
            await dec_repo.record_decision(
                tenant_id,
                task_id=task_id,
                classification="APPROVAL_VALIDATION",
                risk_score=risk_score,
                risk_level=risk_level,
                eligibility="DENIED",
                requires_human_gate=True,
                decision_reason=reason_msg,
                reasons=["Validation failed during approval processing"]
            )

        # 3. Status transition guard / Replay protection
        current_status = approval_record["status"]
        if current_status != "PENDING":
            if current_status in ["APPROVED", "REJECTED"]:
                await log_failure("Reused token")
                await session.commit()
                raise ValueError("Reused token")
            await log_failure("Invalid status transition")
            await session.commit()
            raise ValueError("Invalid status transition")

        # 4. Expiration check
        now = datetime.now(timezone.utc)
        expires_at = approval_record["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            # Update approval to EXPIRED
            await app_repo.submit_approval(tenant_id, approval_id, "EXPIRED", "Approval token expired", "system")
            await log_failure("Expired token")
            await session.commit()
            raise ValueError("Expired token")

        # 5. One-time token check (support both full and short token)
        stored_token = approval_record["token"]
        if not token or len(token) < 8:
            await log_failure("Invalid token format")
            await session.commit()
            raise ValueError("Invalid token format")
        if not (stored_token == token or stored_token.startswith(token)):
            await log_failure("Wrong token")
            await session.commit()
            raise ValueError("Wrong token")

        # 6. Action hash consistency check
        if approval_record["action_hash"] != action_hash:
            await log_failure("Wrong action hash")
            await session.commit()
            raise ValueError("Wrong action hash")

        # Everything is valid! Record approval decision
        final_status = "APPROVED" if status.upper() == "APPROVED" else "REJECTED"
        
        # Submit approval to DB
        updated_approval = await app_repo.submit_approval(
            tenant_id=tenant_id,
            approval_id=approval_id,
            status=final_status,
            reason=f"Validated Telegram Response: {final_status}",
            approved_by=approved_by
        )

        # 7. Move task state to PENDING_APPROVED if APPROVED
        if final_status == "APPROVED":
            await task_repo.update_task_status(tenant_id, task_id, "PENDING_APPROVED")
        
        # Log successful event
        audit_status = "ALLOWED" if final_status == "APPROVED" else "DENIED"
        await audit_repo.log_audit(
            tenant_id,
            event_type="APPROVAL_DECISION_PROCESSED",
            actor_id=approved_by,
            actor_type="HUMAN",
            action="APPROVE" if final_status == "APPROVED" else "REJECT",
            target=f"task:{task_id}",
            status=audit_status,
            risk_level=risk_level,
            before_state={"approval_id": approval_id, "status": "PENDING"},
            after_state={"approval_id": approval_id, "status": final_status}
        )

        await dec_repo.record_decision(
            tenant_id,
            task_id=task_id,
            classification="APPROVAL_DECISION",
            risk_score=risk_score,
            risk_level=risk_level,
            eligibility=final_status,
            requires_human_gate=True,
            decision_reason=f"Telegram human approval: {final_status}",
            reasons=[f"Completed approval check successfully. Verdict: {final_status}"]
        )

        return updated_approval
