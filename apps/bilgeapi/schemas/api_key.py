from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

ApiKeyRole = Literal["ADMIN", "OPERATOR", "AUDIT_OBSERVER", "SOVEREIGN_PRIME"]

class ApiKeyCreate(BaseModel):
    role: ApiKeyRole = Field(..., description="Role assigned to this API key (e.g. ADMIN, OPERATOR, AUDIT_OBSERVER)")
    description: Optional[str] = Field(None, description="Purpose of this API key")
    tenant_id: Optional[str] = Field(None, description="Optional tenant/workspace owner for this API key")
    expires_in_days: Optional[int] = Field(None, description="Optional lifetime of the key in days")
    quota_daily: Optional[int] = Field(None, description="Daily usage quota (None/null = unlimited, 0 = blocked, >0 = limit)")
    quota_monthly: Optional[int] = Field(None, description="Monthly usage quota (None/null = unlimited, 0 = blocked, >0 = limit)")

class ApiKeyResponse(BaseModel):
    id: str
    key_prefix: str
    key_fingerprint: str
    role: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    is_active: bool
    created_by: Optional[str] = None
    revoked_by: Optional[str] = None
    revoke_reason: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    quota_daily: Optional[int] = None
    quota_monthly: Optional[int] = None

    model_config = {


        "from_attributes": True


    }

class ApiKeyCreateResponse(ApiKeyResponse):
    plaintext_key: str = Field(..., description="Plaintext API key. Only returned once upon creation.")

class ApiKeyRevoke(BaseModel):
    reason: str = Field(..., min_length=1, description="Reason for revoking this key")

class ApiKeyQuotaUpdate(BaseModel):
    quota_daily: Optional[int] = Field(None, description="Daily quota limit. Set to None/null for unlimited, 0 to block, >0 for active limit.")
    quota_monthly: Optional[int] = Field(None, description="Monthly quota limit. Set to None/null for unlimited, 0 to block, >0 for active limit.")

class ApiKeyQuotaUsageResponse(BaseModel):
    key_id: str
    quota_daily: Optional[int] = None
    quota_monthly: Optional[int] = None
    daily_used: int
    monthly_used: int
    daily_remaining: Optional[int] = None
    monthly_remaining: Optional[int] = None
