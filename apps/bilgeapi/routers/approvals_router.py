import os
import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from apps.bilgeapi.core.workspace import WorkspaceManager
from apps.bilgeapi.memory.db import get_workspace_db_session
from apps.bilgeapi.governance.approval_engine import ApprovalEngine

logger = logging.getLogger("bilgeapi.routers.approvals")

router = APIRouter(prefix="/v1")

class ApprovalSubmitRequest(BaseModel):
    token: str
    status: str  # APPROVED or REJECTED
    chat_id: str
    action_hash: str
    approved_by: str

@router.post("/workspace/approvals/{approval_id}/submit", tags=["Approvals"])
async def submit_approval_direct(
    approval_id: str,
    body: ApprovalSubmitRequest,
    request: Request
):
    """
    Directly submits an approval decision.
    Validates X-Telegram-Bot-Api-Secret-Token header if webhook secret is configured.
    """
    secret_token = os.getenv("BILGEAPI_TELEGRAM_WEBHOOK_SECRET") or os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    if secret_token:
        header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header_token != secret_token:
            logger.warning("Invalid X-Telegram-Bot-Api-Secret-Token header received on submit endpoint")
            raise HTTPException(status_code=403, detail="Unauthorized")

    workspace_dir = WorkspaceManager().workspace_dir

    async with get_workspace_db_session(workspace_dir) as session:
        try:
            result = await ApprovalEngine.validate_and_submit_approval(
                approval_id=approval_id,
                token=body.token,
                status=body.status,
                chat_id=body.chat_id,
                action_hash=body.action_hash,
                approved_by=body.approved_by,
                session=session
            )
            return {"status": "success", "approval_id": approval_id, "verdict": body.status}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/telegram/webhook", tags=["Approvals"])
async def telegram_webhook(
    request: Request
):
    """
    Webhook endpoint for Telegram Updates.
    Processes only callback_query type updates.
    """
    secret_token = os.getenv("BILGEAPI_TELEGRAM_WEBHOOK_SECRET") or os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    if secret_token:
        header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header_token != secret_token:
            logger.warning("Invalid X-Telegram-Bot-Api-Secret-Token header received on webhook")
            raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Constraint 2: allowed_updates restricted to callback_query
    if "callback_query" not in payload:
        return {"status": "ignored"}

    callback_query = payload["callback_query"]
    data = callback_query.get("data", "")
    
    # Expected callback data format: approve:<approval_id>:<short_token> or reject:<approval_id>:<short_token>
    parts = data.split(":")
    if len(parts) != 3 or parts[0] not in ["approve", "reject"]:
        return {"status": "ignored"}

    action_type, approval_id, short_token = parts
    status = "APPROVED" if action_type == "approve" else "REJECTED"
    
    from_user = callback_query.get("from", {})
    chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))
    if not chat_id:
        chat_id = str(from_user.get("id", ""))
    
    approved_by = from_user.get("username") or from_user.get("first_name") or "Telegram User"

    workspace_dir = WorkspaceManager().workspace_dir

    async with get_workspace_db_session(workspace_dir) as session:
        # Fetch approval to extract its action_hash
        from sqlalchemy import select
        from apps.bilgeapi.memory.models import ApprovalModel
        stmt = select(ApprovalModel).where(ApprovalModel.id == approval_id)
        res = await session.execute(stmt)
        db_approval = res.scalar_one_or_none()
        if not db_approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        
        action_hash = db_approval.action_hash

        user_id = str(from_user.get("id", ""))

        try:
            result = await ApprovalEngine.validate_and_submit_approval(
                approval_id=approval_id,
                token=short_token,
                status=status,
                chat_id=chat_id,
                action_hash=action_hash,
                approved_by=approved_by,
                session=session,
                user_id=user_id
            )
            return {"status": "success", "approval_id": approval_id, "verdict": status}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
