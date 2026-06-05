from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class DispatchStatus(str, Enum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    FAILED = "FAILED"

class RepairRequestCreate(BaseModel):
    requested_by: str
    risk_score: float
    risk_reason: str
    approval_required: bool = True
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class RepairRequestResponse(BaseModel):
    id: str
    diagnostic_id: str
    requested_by: str
    approved_by: Optional[str] = None
    approval_status: ApprovalStatus
    risk_score: float
    risk_reason: str
    dispatch_status: DispatchStatus
    external_reference: Optional[str] = None
    approval_required: bool
    rejection_reason: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class RepairApprovalRequest(BaseModel):
    webhook_url: Optional[str] = None

class RepairRejectionRequest(BaseModel):
    rejection_reason: str

class RepairDispatchRequest(BaseModel):
    adapter: str = "webhook"
    webhook_url: Optional[str] = None
    dry_run: bool = False

