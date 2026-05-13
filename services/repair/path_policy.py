from __future__ import annotations

from services.repair.repair_models import DEFAULT_FORBIDDEN_PATHS


def normalize_path(path: str) -> str:
    return str(path or "").strip().strip("'\"").replace("\\", "/").lstrip("./").lower()


def is_forbidden_path(path: str, forbidden_paths: list[str] | None = None) -> bool:
    normalized = normalize_path(path)
    for forbidden in forbidden_paths or DEFAULT_FORBIDDEN_PATHS:
        forbidden_norm = normalize_path(forbidden).rstrip("/")
        if not forbidden_norm:
            continue
        if normalized == forbidden_norm or normalized.startswith(forbidden_norm + "/"):
            return True
    return False


def evaluate_changed_paths(changed_files: list[str], forbidden_paths: list[str] | None = None) -> dict:
    blocked = [path for path in changed_files if is_forbidden_path(path, forbidden_paths)]
    return {
        "allowed": not blocked,
        "blocked_paths": blocked,
        "status": "AUTO_REPAIR_BLOCKED" if blocked else "PATHS_ALLOWED",
        "recommended_action": "Manual senior review required" if blocked else "Continue verification",
    }

