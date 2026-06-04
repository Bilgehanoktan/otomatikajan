from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class WebhookTestRequest(BaseModel):
    webhook_url: str = Field(..., description="Target URL for testing webhook dispatch")
    payload: Optional[Dict[str, Any]] = Field(None, description="Custom dictionary payload to send")

class WebhookTestResponse(BaseModel):
    status: str = Field(..., description="Workflow delivery outcome (SENT, FAILED, or DEAD_LETTER)")
    resolved_ip: Optional[str] = Field(None, description="The resolved target server IP address")
    signature: str = Field(..., description="The generated HMAC-SHA256 signature header")
    status_code: Optional[float] = Field(None, description="The returned HTTP status code")
    error_message: Optional[str] = Field(None, description="Error details if delivery failed")
    timestamp: str = Field(..., description="ISO 8601 timestamp sent in X-BilgeAPI-Timestamp")
    idempotency_key: str = Field(..., description="Unique key sent in X-BilgeAPI-Idempotency-Key")

class WebhookDeliveryResponse(BaseModel):
    id: str
    repair_request_id: str
    webhook_url: str
    status_code: Optional[float] = None
    delivery_status: str
    error_message: Optional[str] = None
    payload_hash: str
    attempt_count: float
    created_at: datetime
