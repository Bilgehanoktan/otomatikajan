from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ReviewLedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chain_id: str
    sequence_no: int
    event_type: str
    entity_type: str
    entity_id: str
    actor_id: Optional[str] = None
    previous_hash: Optional[str] = None
    payload_hash: str
    event_hash: str
    payload_summary: Optional[Dict[str, Any]] = None
    created_at: datetime


class ReviewLedgerChainResponse(BaseModel):
    chain_id: str
    entries: List[ReviewLedgerEntryResponse]


class ReviewLedgerVerifyResponse(BaseModel):
    chain_id: str
    valid: bool
    entry_count: int
    head_hash: Optional[str] = None
    issues: List[Dict[str, Any]] = []


class ReviewLedgerAppendRequest(BaseModel):
    chain_id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_id: Optional[str] = None
    payload: Dict[str, Any] = {}


class ReviewLedgerExportResponse(BaseModel):
    chain_id: str
    format: str
    valid: bool
    entry_count: int
    content: str
