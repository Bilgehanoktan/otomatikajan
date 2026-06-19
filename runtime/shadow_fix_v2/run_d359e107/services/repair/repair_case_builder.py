from __future__ import annotations

from typing import Any

from services.repair.evidence_pack import get_repo_snapshot
from services.repair.repair_models import DEFAULT_FORBIDDEN_PATHS, RepairCase


DEFAULT_ALLOWED_PATHS = ["services/", "libs/", "apps/", "tests/", "workers/", "scripts/"]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def build_repair_case(input_payload: dict[str, Any]) -> RepairCase:
    incident_id = str(input_payload.get("incident_id") or input_payload.get("id") or "INC-UNKNOWN")
    forbidden_paths = _string_list(input_payload.get("forbidden_paths")) or list(DEFAULT_FORBIDDEN_PATHS)
    allowed_paths = _string_list(input_payload.get("allowed_paths")) or list(DEFAULT_ALLOWED_PATHS)

    return RepairCase(
        incident_id=incident_id,
        trace_id=str(input_payload.get("trace_id") or ""),
        error_type=str(input_payload.get("error_type") or input_payload.get("exception") or ""),
        summary=str(input_payload.get("summary") or input_payload.get("message") or ""),
        failed_command=str(input_payload.get("failed_command") or ""),
        failed_test=str(input_payload.get("failed_test") or ""),
        traceback=str(input_payload.get("traceback") or ""),
        related_logs=_string_list(input_payload.get("related_logs") or input_payload.get("logs")),
        repo_snapshot=input_payload.get("repo_snapshot") or get_repo_snapshot(),
        allowed_paths=allowed_paths,
        forbidden_paths=forbidden_paths,
        suspected_files=_string_list(input_payload.get("suspected_files")),
    )
