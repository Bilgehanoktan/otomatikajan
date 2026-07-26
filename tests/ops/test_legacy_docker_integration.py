from __future__ import annotations

import json
import os
import re
from pathlib import Path

from scripts.recovery.legacy_docker_integration import (
    build_redis_merge_plan,
    discover_redis_snapshots,
    write_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_snapshot(
    root: Path,
    volume_id: str,
    content: bytes,
    mtime_ns: int,
) -> Path:
    snapshot = root / volume_id / "_data" / "dump.rdb"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(content)
    snapshot_stat = snapshot.stat()
    os.utime(snapshot, ns=(snapshot_stat.st_atime_ns, mtime_ns))
    return snapshot


def test_compose_uses_named_redis_volume() -> None:
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    redis_block = compose.split("\n  redis:\n", maxsplit=1)[1].split(
        "\n  worker:\n", maxsplit=1
    )[0]
    volumes_block = compose.split("\nvolumes:\n", maxsplit=1)[1]

    assert "- redis_data:/data" in redis_block
    assert re.search(r"(?m)^  redis_data:\s*$", volumes_block)


def test_snapshot_discovery_hashes_and_sorts_newest_first(tmp_path: Path) -> None:
    older = _write_snapshot(tmp_path, "a" * 64, b"REDIS0012-old", 100)
    newer = _write_snapshot(tmp_path, "b" * 64, b"REDIS0012-new", 200)

    snapshots = discover_redis_snapshots(tmp_path, source="legacy")

    assert [item.path for item in snapshots] == [newer, older]
    assert snapshots[0].source == "legacy"
    assert snapshots[0].size_bytes == len(b"REDIS0012-new")
    assert len(snapshots[0].sha256) == 64


def test_merge_plan_preserves_active_and_deduplicates_legacy(tmp_path: Path) -> None:
    active_root = tmp_path / "active"
    legacy_root = tmp_path / "legacy"
    _write_snapshot(active_root, "1" * 64, b"REDIS0012-active-old", 100)
    active_new = _write_snapshot(active_root, "2" * 64, b"REDIS0012-active-new", 300)
    _write_snapshot(legacy_root, "3" * 64, b"REDIS0012-active-new", 250)
    legacy_unique = _write_snapshot(legacy_root, "4" * 64, b"REDIS0012-legacy", 200)

    plan = build_redis_merge_plan(
        discover_redis_snapshots(active_root, source="active"),
        discover_redis_snapshots(legacy_root, source="legacy"),
    )

    assert plan.policy == "active_wins"
    assert plan.base.path == active_new
    assert len(plan.active_candidates) == 1
    assert [item.path for item in plan.legacy_candidates] == [legacy_unique]


def test_manifest_is_atomic_and_contains_no_file_contents(tmp_path: Path) -> None:
    active_root = tmp_path / "active"
    _write_snapshot(active_root, "5" * 64, b"REDIS0012-secret-payload", 100)
    plan = build_redis_merge_plan(
        discover_redis_snapshots(active_root, source="active"), []
    )
    output = tmp_path / "manifest.json"

    write_manifest(output, plan)

    manifest = json.loads(output.read_text(encoding="utf-8"))
    serialized = json.dumps(manifest)
    assert manifest["redis"]["policy"] == "active_wins"
    assert manifest["redis"]["base"]["volume_id"] == "5" * 64
    assert "secret-payload" not in serialized
