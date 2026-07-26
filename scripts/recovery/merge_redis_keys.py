from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from typing import Protocol
from urllib.parse import urlsplit

from redis import Redis
from redis.exceptions import ResponseError


class RedisSource(Protocol):
    def scan_iter(self, count: int = 500): ...

    def dump(self, key: bytes) -> bytes | None: ...

    def pttl(self, key: bytes) -> int: ...


class RedisTarget(Protocol):
    def restore(
        self,
        key: bytes,
        ttl: int,
        payload: bytes,
        *,
        replace: bool,
    ) -> None: ...


@dataclass(frozen=True)
class MergeStats:
    scanned: int = 0
    restored: int = 0
    conflicts: int = 0
    skipped: int = 0


def merge_missing_keys(
    source: RedisSource,
    target: RedisTarget,
    *,
    scan_count: int = 500,
) -> MergeStats:
    if scan_count <= 0:
        raise ValueError("scan_count must be positive")

    scanned = restored = conflicts = skipped = 0
    for key in source.scan_iter(count=scan_count):
        scanned += 1
        payload = source.dump(key)
        if payload is None:
            skipped += 1
            continue

        pttl = source.pttl(key)
        if pttl == -2:
            skipped += 1
            continue
        ttl = max(pttl, 0)

        try:
            target.restore(key, ttl, payload, replace=False)
            restored += 1
        except ResponseError as exc:
            if str(exc).startswith("BUSYKEY"):
                conflicts += 1
                continue
            raise

    return MergeStats(
        scanned=scanned,
        restored=restored,
        conflicts=conflicts,
        skipped=skipped,
    )


def _redis_url_from_env(variable: str) -> str:
    value = os.environ.get(variable)
    if not value:
        raise ValueError(f"Required environment variable is missing: {variable}")
    parsed = urlsplit(value)
    if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
        raise ValueError(f"Invalid Redis URL in environment variable: {variable}")
    return value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge missing Redis keys while preserving target values."
    )
    parser.add_argument("--source-url-env", default="SOURCE_REDIS_URL")
    parser.add_argument("--target-url-env", default="REDIS_URL")
    parser.add_argument("--scan-count", type=int, default=500)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    source = Redis.from_url(
        _redis_url_from_env(args.source_url_env),
        decode_responses=False,
        socket_connect_timeout=10,
        socket_timeout=10,
    )
    target = Redis.from_url(
        _redis_url_from_env(args.target_url_env),
        decode_responses=False,
        socket_connect_timeout=10,
        socket_timeout=10,
    )
    try:
        source.ping()
        target.ping()
        result = merge_missing_keys(source, target, scan_count=args.scan_count)
    finally:
        source.close()
        target.close()

    print(json.dumps(asdict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
