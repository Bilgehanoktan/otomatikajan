from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Sequence


SnapshotSource = Literal["active", "legacy"]
VOLUME_ID_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RedisSnapshot:
    source: SnapshotSource
    volume_id: str
    path: Path
    size_bytes: int
    mtime_ns: int
    sha256: str


@dataclass(frozen=True)
class RedisMergePlan:
    policy: str
    base: RedisSnapshot
    active_candidates: tuple[RedisSnapshot, ...]
    legacy_candidates: tuple[RedisSnapshot, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover_redis_snapshots(root: Path, *, source: SnapshotSource) -> list[RedisSnapshot]:
    if source not in {"active", "legacy"}:
        raise ValueError(f"Unsupported snapshot source: {source}")

    root = root.resolve(strict=True)
    snapshots: list[RedisSnapshot] = []
    for candidate in root.glob("*/_data/dump.rdb"):
        if candidate.is_symlink():
            raise ValueError(f"Symlink snapshots are not allowed: {candidate}")

        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(root):
            raise ValueError(f"Snapshot escapes root: {candidate}")

        volume_id = candidate.parents[1].name
        if not VOLUME_ID_PATTERN.fullmatch(volume_id):
            continue

        with resolved.open("rb") as handle:
            if handle.read(5) != b"REDIS":
                raise ValueError(f"Invalid Redis RDB header: {candidate}")

        stat = resolved.stat()
        snapshots.append(
            RedisSnapshot(
                source=source,
                volume_id=volume_id,
                path=resolved,
                size_bytes=stat.st_size,
                mtime_ns=stat.st_mtime_ns,
                sha256=_sha256(resolved),
            )
        )

    return sorted(snapshots, key=lambda item: (item.mtime_ns, item.volume_id), reverse=True)


def _deduplicate(
    snapshots: Sequence[RedisSnapshot],
    known_hashes: set[str],
) -> tuple[RedisSnapshot, ...]:
    result: list[RedisSnapshot] = []
    for snapshot in snapshots:
        if snapshot.sha256 in known_hashes:
            continue
        known_hashes.add(snapshot.sha256)
        result.append(snapshot)
    return tuple(result)


def build_redis_merge_plan(
    active_snapshots: Sequence[RedisSnapshot],
    legacy_snapshots: Sequence[RedisSnapshot],
) -> RedisMergePlan:
    if not active_snapshots:
        raise ValueError("At least one active Redis snapshot is required")

    active_sorted = sorted(
        active_snapshots,
        key=lambda item: (item.mtime_ns, item.volume_id),
        reverse=True,
    )
    legacy_sorted = sorted(
        legacy_snapshots,
        key=lambda item: (item.mtime_ns, item.volume_id),
        reverse=True,
    )
    base = active_sorted[0]
    known_hashes = {base.sha256}
    active_candidates = _deduplicate(active_sorted[1:], known_hashes)
    legacy_candidates = _deduplicate(legacy_sorted, known_hashes)
    return RedisMergePlan(
        policy="active_wins",
        base=base,
        active_candidates=active_candidates,
        legacy_candidates=legacy_candidates,
    )


def _snapshot_payload(snapshot: RedisSnapshot) -> dict[str, object]:
    return {
        "source": snapshot.source,
        "volume_id": snapshot.volume_id,
        "path": str(snapshot.path),
        "size_bytes": snapshot.size_bytes,
        "mtime_ns": snapshot.mtime_ns,
        "sha256": snapshot.sha256,
    }


def write_manifest(output: Path, plan: RedisMergePlan) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "redis": {
            "policy": plan.policy,
            "base": _snapshot_payload(plan.base),
            "active_candidates": [
                _snapshot_payload(item) for item in plan.active_candidates
            ],
            "legacy_candidates": [
                _snapshot_payload(item) for item in plan.legacy_candidates
            ],
        },
    }

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temporary_path = Path(handle.name)
        os.replace(temporary_path, output)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a safe Redis snapshot merge manifest for Docker recovery."
    )
    parser.add_argument("--active-root", required=True, type=Path)
    parser.add_argument("--legacy-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    plan = build_redis_merge_plan(
        discover_redis_snapshots(args.active_root, source="active"),
        discover_redis_snapshots(args.legacy_root, source="legacy"),
    )
    write_manifest(args.output, plan)
    print(
        json.dumps(
            {
                "manifest": str(args.output.resolve()),
                "active_candidates": len(plan.active_candidates),
                "legacy_candidates": len(plan.legacy_candidates),
                "policy": plan.policy,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
