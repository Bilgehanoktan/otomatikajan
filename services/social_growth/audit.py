"""EpisodeRecord/ActionRecord persistence for social-growth operations."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from services.orchestration.domain.models import (
    ActionRecord,
    EpisodeRecord,
    VerificationReport,
)
from services.social_growth.contracts import OperationEvidence, OperationStatus


class EpisodeEvidenceSink:
    """Append redacted operation evidence as governed episode JSONL."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()

    def record(self, evidence: OperationEvidence) -> None:
        """Persist one operation as an ActionRecord inside an EpisodeRecord."""

        succeeded = evidence.status is OperationStatus.SUCCEEDED
        action = ActionRecord(
            plan_id="social-growth",
            step_id=evidence.operation,
            tool_used=str(evidence.metadata.get("tool_used", "MetaGraphClient")),
            agent_id="social_growth",
            input_data={"metadata": evidence.metadata},
            output_data={
                "status": evidence.status.value,
                "provider_id": evidence.provider_id,
                "reason": evidence.reason,
            },
            success=succeeded,
            errors=[] if succeeded else [evidence.reason or evidence.status.value],
            trace_ref=evidence.provider_id,
            timestamp=evidence.occurred_at,
        )
        verification = VerificationReport(
            result_status=succeeded,
            evidence_summary=(
                f"{evidence.operation}:{evidence.status.value}:"
                f"{evidence.provider_id or 'no-provider-id'}"
            ),
            unresolved_risks=[] if succeeded else [evidence.reason or evidence.status.value],
            confidence_adjusted=1.0 if succeeded else 0.0,
            integration_reality_score=1.0 if succeeded else 0.0,
            safe_to_finalize=True,
            safe_to_learn=succeeded,
        )
        episode = EpisodeRecord(
            actions=[action],
            verification=verification,
            final_output=action.output_data,
            lessons_learned=[verification.evidence_summary],
            timestamp=evidence.occurred_at,
        )
        serialized = json.dumps(asdict(episode), ensure_ascii=False, default=_json_default)
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as evidence_file:
                evidence_file.write(serialized + "\n")


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return str(value)
