from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from redis.exceptions import ResponseError

from scripts.recovery.merge_redis_keys import merge_missing_keys


@dataclass
class FakeSource:
    payloads: dict[bytes, bytes | None]
    ttls: dict[bytes, int]

    def scan_iter(self, count: int = 500):
        del count
        return iter(self.payloads)

    def dump(self, key: bytes) -> bytes | None:
        return self.payloads[key]

    def pttl(self, key: bytes) -> int:
        return self.ttls[key]


@dataclass
class FakeTarget:
    existing: set[bytes] = field(default_factory=set)
    restored: list[tuple[bytes, int, bytes]] = field(default_factory=list)

    def restore(
        self,
        key: bytes,
        ttl: int,
        payload: bytes,
        *,
        replace: bool,
    ) -> None:
        assert replace is False
        if key in self.existing:
            raise ResponseError("BUSYKEY Target key name already exists.")
        self.existing.add(key)
        self.restored.append((key, ttl, payload))


def test_merge_preserves_existing_target_keys_and_ttl() -> None:
    source = FakeSource(
        payloads={b"active": b"old-active", b"legacy": b"legacy-value"},
        ttls={b"active": -1, b"legacy": 25_000},
    )
    target = FakeTarget(existing={b"active"})

    result = merge_missing_keys(source, target)

    assert result.scanned == 2
    assert result.restored == 1
    assert result.conflicts == 1
    assert result.skipped == 0
    assert target.restored == [(b"legacy", 25_000, b"legacy-value")]


def test_merge_uses_zero_ttl_for_persistent_keys() -> None:
    source = FakeSource(payloads={b"persistent": b"payload"}, ttls={b"persistent": -1})
    target = FakeTarget()

    result = merge_missing_keys(source, target)

    assert result.restored == 1
    assert target.restored == [(b"persistent", 0, b"payload")]


def test_merge_skips_keys_that_expire_during_scan() -> None:
    source = FakeSource(payloads={b"expired": None}, ttls={b"expired": -2})

    result = merge_missing_keys(source, FakeTarget())

    assert result.scanned == 1
    assert result.skipped == 1
    assert result.restored == 0


def test_merge_does_not_hide_unexpected_redis_errors() -> None:
    class BrokenTarget(FakeTarget):
        def restore(self, *args, **kwargs) -> None:
            raise ResponseError("ERR invalid payload")

    source = FakeSource(payloads={b"key": b"payload"}, ttls={b"key": -1})

    with pytest.raises(ResponseError, match="invalid payload"):
        merge_missing_keys(source, BrokenTarget())
