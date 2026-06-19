from __future__ import annotations

import re
from pathlib import Path

from services.repair.evidence_pack import REPO_ROOT, recent_changed_files
from services.repair.repair_models import RepairCase


_PY_PATH_RE = re.compile(r"(?P<path>(?:[A-Za-z]:)?[^:\n\r\"]+?\.py)")


def _normalize_path(path: str) -> str:
    cleaned = path.strip().strip("'\"").replace("\\", "/")
    marker_index = min(
        [idx for marker in ("/services/", "/libs/", "/apps/", "/tests/", "/workers/", "/scripts/") if (idx := cleaned.find(marker)) >= 0]
        or [-1]
    )
    if marker_index >= 0:
        cleaned = cleaned[marker_index + 1 :]
    return cleaned.lstrip("./")


def _is_under(path: str, prefixes: list[str]) -> bool:
    if not prefixes:
        return True
    normalized = _normalize_path(path)
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def _is_forbidden(path: str, forbidden_paths: list[str]) -> bool:
    normalized = _normalize_path(path).lower()
    for forbidden in forbidden_paths:
        forbidden_norm = _normalize_path(forbidden).lower().rstrip("/")
        if not forbidden_norm:
            continue
        if normalized == forbidden_norm or normalized.startswith(forbidden_norm + "/"):
            return True
    return False


def _extract_paths(text: str) -> set[str]:
    paths: set[str] = set()
    for match in _PY_PATH_RE.finditer(text or ""):
        candidate = _normalize_path(match.group("path"))
        if candidate.endswith(".py"):
            paths.add(candidate)
    return paths


def _failed_test_hints(failed_test: str) -> set[str]:
    hints: set[str] = set()
    text = (failed_test or "").replace("\\", "/")
    hints.update(_extract_paths(text))
    for token in re.split(r"[:\s]+", text):
        if token.endswith(".py"):
            hints.add(_normalize_path(token))
    return hints


def localize_code(repair_case: RepairCase, repo_root: Path | None = None) -> list[dict[str, object]]:
    root = repo_root or REPO_ROOT
    scores: dict[str, dict[str, object]] = {}

    def add_score(path: str, points: int, reason: str) -> None:
        normalized = _normalize_path(path)
        if not normalized or not _is_under(normalized, repair_case.allowed_paths):
            return
        if _is_forbidden(normalized, repair_case.forbidden_paths):
            return
        entry = scores.setdefault(normalized, {"file": normalized, "score": 0, "reasons": []})
        entry["score"] = int(entry["score"]) + points
        entry["reasons"].append(reason)

    for path in _extract_paths(repair_case.traceback):
        add_score(path, 40, "traceback")

    for path in _failed_test_hints(repair_case.failed_test):
        add_score(path, 25, "failed_test")

    log_text = "\n".join(repair_case.related_logs)
    for path in _extract_paths(log_text):
        add_score(path, 15, "related_logs")

    for path in list(scores):
        if _is_under(path, repair_case.allowed_paths):
            add_score(path, 10, "allowed_path")

    for path in recent_changed_files(root):
        if path in scores:
            add_score(path, 10, "recent_changed")

    if repair_case.suspected_files:
        for path in repair_case.suspected_files:
            add_score(path, 20, "payload_suspected_file")

    return sorted(scores.values(), key=lambda item: (-int(item["score"]), str(item["file"])))
