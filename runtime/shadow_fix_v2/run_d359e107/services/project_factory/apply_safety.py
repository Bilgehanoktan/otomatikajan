from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Dict, Any, List


BLOCKED_KEYWORDS = [
    ".env",
    ".pem",
    ".key",
    ".p12",
    "credentials",
    "secret",
    "node_modules/",
    ".git/",
]
BLOCKED_SUFFIXES = [".db"]
MAX_FILE_BYTES = 1_000_000


def assess_delivery_file_safety(relative_path: str, source_file: Path) -> Dict[str, Any]:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    path = PurePosixPath(normalized)
    blocking_risks: List[str] = []
    warnings: List[str] = []

    if path.is_absolute() or ".." in path.parts:
        blocking_risks.append(f"path traversal or absolute path blocked: {relative_path}")

    lowered = normalized.lower()
    if any(keyword in lowered for keyword in BLOCKED_KEYWORDS):
        blocking_risks.append(f"protected path keyword blocked: {relative_path}")

    if any(lowered.endswith(suffix) for suffix in BLOCKED_SUFFIXES):
        blocking_risks.append(f"protected file suffix blocked: {relative_path}")

    if source_file.exists() and source_file.is_file():
        size = source_file.stat().st_size
        if size > MAX_FILE_BYTES:
            blocking_risks.append(f"large file blocked: {relative_path}")
        with open(source_file, "rb") as f:
            if b"\x00" in f.read(4096):
                blocking_risks.append(f"binary file blocked: {relative_path}")
    else:
        blocking_risks.append(f"source file missing: {relative_path}")

    risk = "BLOCKED" if blocking_risks else ("MEDIUM" if warnings else "LOW")
    return {
        "path": normalized,
        "risk": risk,
        "blocking_risks": blocking_risks,
        "warnings": warnings,
    }
