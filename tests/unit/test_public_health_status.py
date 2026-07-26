from apps.public_api.health_status import resolve_health_status


def test_repair_unavailable_degrades_health():
    status, reason = resolve_health_status(
        is_standby=False,
        db_ok=True,
        memory_exceeded=False,
        repair_available=False,
    )

    assert status == "degraded"
    assert reason == "repair_unavailable"


def test_primary_health_failures_keep_priority_over_repair():
    status, reason = resolve_health_status(
        is_standby=False,
        db_ok=False,
        memory_exceeded=False,
        repair_available=False,
    )

    assert status == "degraded"
    assert reason == "db_failed"


def test_standby_status_has_highest_priority():
    status, reason = resolve_health_status(
        is_standby=True,
        db_ok=False,
        memory_exceeded=True,
        repair_available=False,
    )

    assert status == "standby"
    assert reason == "standby"
