from __future__ import annotations


def attempts_allowed(retry: int) -> int:
    return max(1, int(retry) + 1)


def should_retry(attempt: int, retry: int) -> bool:
    return int(attempt) < attempts_allowed(retry)

