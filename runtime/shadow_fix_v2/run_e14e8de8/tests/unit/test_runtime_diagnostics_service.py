from services.workflow_api.runtime_diagnostics import RuntimeDiagnosticsService


def _ids(findings):
    return {finding.id: finding for finding in findings}


def test_full_stack_profile_mismatch_is_operator_action():
    findings = _ids(
        RuntimeDiagnosticsService(
            config={
                "APP_ENV": "development",
                "RUNTIME_PROFILE": "full-stack-local",
                "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
                "QUEUE_BACKEND": "inprocess",
                "REDIS_ENABLED": False,
                "CELERY_ENABLED": False,
                "EPHEMERAL_WORKFLOWS_ENABLED": False,
                "INPROCESS_JOB_WORKERS_ENABLED": False,
            },
        ).collect()
    )

    finding = findings["profile_mismatch"]
    assert finding.severity == "error"
    assert finding.auto_repairable is False
    assert finding.requires_operator_action is True


def test_observer_role_write_denial_is_reported():
    findings = _ids(
        RuntimeDiagnosticsService(
            config={
                "RUNTIME_PROFILE": "local-dev",
                "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
                "QUEUE_BACKEND": "inprocess",
                "REDIS_ENABLED": False,
                "CELERY_ENABLED": False,
                "EPHEMERAL_WORKFLOWS_ENABLED": False,
                "INPROCESS_JOB_WORKERS_ENABLED": True,
            },
            identity_role="AUDIT_OBSERVER",
        ).collect()
    )

    finding = findings["observer_write_denied"]
    assert finding.severity == "warning"
    assert finding.requires_operator_action is True
    assert "OPERATOR" in finding.recommended_action


def test_local_dev_sqlite_fallback_explains_hidden_docker_workflows():
    findings = _ids(
        RuntimeDiagnosticsService(
            config={
                "RUNTIME_PROFILE": "local-dev",
                "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
                "QUEUE_BACKEND": "inprocess",
                "REDIS_ENABLED": False,
                "CELERY_ENABLED": False,
                "EPHEMERAL_WORKFLOWS_ENABLED": False,
                "INPROCESS_JOB_WORKERS_ENABLED": True,
            },
            db_is_fallback=False,
        ).collect()
    )

    finding = findings["db_fallback_active"]
    assert finding.severity == "info"
    assert "Docker Postgres" in finding.impact


def test_inprocess_queue_without_workers_is_auto_repairable():
    findings = _ids(
        RuntimeDiagnosticsService(
            config={
                "RUNTIME_PROFILE": "local-dev",
                "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
                "QUEUE_BACKEND": "inprocess",
                "REDIS_ENABLED": False,
                "CELERY_ENABLED": False,
                "EPHEMERAL_WORKFLOWS_ENABLED": False,
                "INPROCESS_JOB_WORKERS_ENABLED": False,
            },
            queue_stats={"workers": 0, "pending": 2},
        ).collect()
    )

    finding = findings["queue_workers_disabled"]
    assert finding.severity == "warning"
    assert finding.auto_repairable is True


def test_ephemeral_workflow_mode_is_warning():
    findings = _ids(
        RuntimeDiagnosticsService(
            config={
                "RUNTIME_PROFILE": "local-dev",
                "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
                "QUEUE_BACKEND": "inprocess",
                "REDIS_ENABLED": False,
                "CELERY_ENABLED": False,
                "EPHEMERAL_WORKFLOWS_ENABLED": True,
                "INPROCESS_JOB_WORKERS_ENABLED": True,
            },
        ).collect()
    )

    finding = findings["ephemeral_workflow_enabled"]
    assert finding.severity == "warning"
    assert finding.requires_operator_action is True


def test_active_signoff_serialization_fingerprints_are_repairable():
    findings = _ids(
        RuntimeDiagnosticsService(
            config={
                "RUNTIME_PROFILE": "local-dev",
                "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
                "QUEUE_BACKEND": "inprocess",
                "REDIS_ENABLED": False,
                "CELERY_ENABLED": False,
                "EPHEMERAL_WORKFLOWS_ENABLED": False,
                "INPROCESS_JOB_WORKERS_ENABLED": True,
            },
            active_error_fingerprints={
                "count": 2,
                "recurrence_total": 11,
                "signoff_serialization_only": True,
                "top": [],
            },
        ).collect()
    )

    finding = findings["active_error_fingerprints"]
    assert finding.severity == "error"
    assert finding.auto_repairable is True
    assert finding.requires_operator_action is False


def test_api_redirect_noise_disappears_after_repair():
    from services.workflow_api.runtime_diagnostics import (
        _API_REDIRECT_NOISE_REPAIRED,
        mark_api_redirect_noise_repaired,
    )
    
    # 1. Initially it should be active
    findings = _ids(
        RuntimeDiagnosticsService(
            config={
                "RUNTIME_PROFILE": "local-dev",
                "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
                "QUEUE_BACKEND": "inprocess",
                "REDIS_ENABLED": False,
                "CELERY_ENABLED": False,
                "EPHEMERAL_WORKFLOWS_ENABLED": False,
                "INPROCESS_JOB_WORKERS_ENABLED": True,
            }
        ).collect()
    )
    assert "api_redirect_noise" in findings
    
    # 2. Trigger repair
    mark_api_redirect_noise_repaired()
    
    # 3. Now it should not be in active diagnostics
    findings_after = _ids(
        RuntimeDiagnosticsService(
            config={
                "RUNTIME_PROFILE": "local-dev",
                "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
                "QUEUE_BACKEND": "inprocess",
                "REDIS_ENABLED": False,
                "CELERY_ENABLED": False,
                "EPHEMERAL_WORKFLOWS_ENABLED": False,
                "INPROCESS_JOB_WORKERS_ENABLED": True,
            }
        ).collect()
    )
    assert "api_redirect_noise" not in findings_after
