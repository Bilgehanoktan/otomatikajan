from typing import Optional, Tuple


def resolve_health_status(
    *,
    is_standby: bool,
    db_ok: bool,
    memory_exceeded: bool,
    repair_available: bool,
) -> Tuple[str, Optional[str]]:
    if is_standby:
        return "standby", "standby"
    if memory_exceeded:
        return "degraded", "memory_limit_exceeded"
    if not db_ok:
        return "degraded", "db_failed"
    if not repair_available:
        return "degraded", "repair_unavailable"
    return "ok", None
