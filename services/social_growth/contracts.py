"""Evidence and status contracts for external social operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class OperationStatus(str, Enum):
    """Canonical result states; only SUCCEEDED means a provider confirmed the action."""

    BLOCKED = "BLOCKED"
    DRY_RUN = "DRY_RUN"
    DUPLICATE = "DUPLICATE"
    FAILED = "FAILED"
    IGNORED = "IGNORED"
    SUCCEEDED = "SUCCEEDED"


class EvidenceError(ValueError):
    """Raised when an evidence record makes an unsupported success claim."""


@dataclass(frozen=True)
class OperationEvidence:
    """Immutable proof record for one external operation."""

    operation: str
    status: OperationStatus
    provider_id: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.operation.strip():
            raise EvidenceError("operation boş olamaz")
        if self.status is OperationStatus.SUCCEEDED and not self.provider_id:
            raise EvidenceError("SUCCEEDED evidence için provider_id zorunludur")
        if self.status is not OperationStatus.SUCCEEDED and self.provider_id:
            raise EvidenceError("provider_id yalnız SUCCEEDED evidence ile kullanılabilir")
        if self.occurred_at.tzinfo is None:
            raise EvidenceError("occurred_at timezone-aware olmalıdır")
