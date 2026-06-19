"""Runtime diagnostics for control-plane self-healing guardrails."""
from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from typing import Any

Severity = str


from services.auth.jwt_auth import is_dev_env

_API_REDIRECT_NOISE_REPAIRED = False


def mark_api_redirect_noise_repaired() -> None:
    """Marks the API redirect noise diagnostic as repaired so it stops rendering in the UI."""
    global _API_REDIRECT_NOISE_REPAIRED
    _API_REDIRECT_NOISE_REPAIRED = True



@dataclass(frozen=True)
class RuntimeDiagnostic:
    id: str
    severity: Severity
    title: str
    evidence: dict[str, Any]
    impact: str
    recommended_action: str
    auto_repairable: bool = False
    requires_operator_action: bool = False
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeDiagnosticsService:
    """Classifies runtime/config/API/auth/queue issues into actionable findings."""

    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
        queue_stats: dict[str, Any] | None = None,
        db_is_fallback: bool = False,
        redis_available: bool | None = None,
        identity_role: str | None = None,
        active_error_fingerprints: dict[str, Any] | None = None,
    ) -> None:
        self.config = config or self._load_config()
        self.queue_stats = queue_stats or {}
        self.db_is_fallback = db_is_fallback
        self.redis_available = redis_available
        self.identity_role = (identity_role or "").upper() or None
        self.active_error_fingerprints = active_error_fingerprints or {}

    @staticmethod
    def _load_config() -> dict[str, Any]:
        from libs.config import (
            APP_ENV,
            CELERY_ENABLED,
            EPHEMERAL_WORKFLOWS_ENABLED,
            INPROCESS_JOB_WORKERS_ENABLED,
            LOCAL_DEV_DB_STRATEGY,
            QUEUE_BACKEND,
            REDIS_ENABLED,
            RUNTIME_PROFILE,
        )

        return {
            "APP_ENV": APP_ENV,
            "RUNTIME_PROFILE": RUNTIME_PROFILE,
            "LOCAL_DEV_DB_STRATEGY": LOCAL_DEV_DB_STRATEGY,
            "QUEUE_BACKEND": QUEUE_BACKEND,
            "REDIS_ENABLED": REDIS_ENABLED,
            "CELERY_ENABLED": CELERY_ENABLED,
            "EPHEMERAL_WORKFLOWS_ENABLED": EPHEMERAL_WORKFLOWS_ENABLED,
            "INPROCESS_JOB_WORKERS_ENABLED": INPROCESS_JOB_WORKERS_ENABLED,
            "SIF_REGISTER_DEFAULT_ROLE": os.getenv("SIF_REGISTER_DEFAULT_ROLE", ""),
        }

    def collect(self) -> list[RuntimeDiagnostic]:
        findings: list[RuntimeDiagnostic] = []
        findings.extend(self._profile_mismatch())
        findings.extend(self._db_fallback())
        findings.extend(self._queue_workers_disabled())
        findings.extend(self._redis_unavailable())
        findings.extend(self._api_redirect_noise())
        findings.extend(self._observer_write_denied())
        findings.extend(self._ephemeral_workflow_enabled())
        findings.extend(self._active_error_fingerprints())
        return findings

    def _profile_mismatch(self) -> Iterable[RuntimeDiagnostic]:
        profile = self.config.get("RUNTIME_PROFILE")
        if profile != "full-stack-local":
            return []

        mismatches = {
            "LOCAL_DEV_DB_STRATEGY": self.config.get("LOCAL_DEV_DB_STRATEGY"),
            "QUEUE_BACKEND": self.config.get("QUEUE_BACKEND"),
            "REDIS_ENABLED": self.config.get("REDIS_ENABLED"),
            "CELERY_ENABLED": self.config.get("CELERY_ENABLED"),
        }
        expected = {
            "LOCAL_DEV_DB_STRATEGY": "primary",
            "QUEUE_BACKEND": "celery",
            "REDIS_ENABLED": True,
            "CELERY_ENABLED": True,
        }
        failed = {key: value for key, value in mismatches.items() if value != expected[key]}
        if not failed:
            return []

        return [
            RuntimeDiagnostic(
                id="profile_mismatch",
                severity="error",
                title="Runtime profile mismatch",
                evidence={"profile": profile, "actual": mismatches, "expected": expected},
                impact="Full-stack mode may read the wrong database or leave workflow workers inactive.",
                recommended_action="Restart with RUNTIME_PROFILE=full-stack-local, LOCAL_DEV_DB_STRATEGY=primary, QUEUE_BACKEND=celery, REDIS_ENABLED=true and CELERY_ENABLED=true.",
                requires_operator_action=True,
                tags=["runtime", "config"],
            )
        ]

    def _db_fallback(self) -> Iterable[RuntimeDiagnostic]:
        strategy = self.config.get("LOCAL_DEV_DB_STRATEGY")
        profile = self.config.get("RUNTIME_PROFILE")
        if self.db_is_fallback:
            return [
                RuntimeDiagnostic(
                    id="db_fallback_active",
                    severity="warning",
                    title="Database fallback active",
                    evidence={"profile": profile, "strategy": strategy, "db_is_fallback": True},
                    impact="Data may be isolated from Docker/Postgres records, so older workflows can disappear from the UI.",
                    recommended_action="Use full-stack-local with LOCAL_DEV_DB_STRATEGY=primary when historical Docker workflows must be visible.",
                    requires_operator_action=True,
                    tags=["database", "runtime"],
                )
            ]

        if profile == "local-dev" and strategy == "sqlite-fallback":
            return [
                RuntimeDiagnostic(
                    id="db_fallback_active",
                    severity="info",
                    title="Local SQLite workflow store",
                    evidence={"profile": profile, "strategy": strategy, "db_is_fallback": False},
                    impact="Local-dev is operational, but it will not show workflows stored in the Docker Postgres database.",
                    recommended_action="Switch to Docker full-stack mode when you need shared Postgres state.",
                    requires_operator_action=True,
                    tags=["database", "runtime"],
                )
            ]
        return []

    def _queue_workers_disabled(self) -> Iterable[RuntimeDiagnostic]:
        backend = self.config.get("QUEUE_BACKEND")
        workers = int(self.queue_stats.get("workers") or 0)
        pending = int(self.queue_stats.get("pending") or self.queue_stats.get("queue_size") or 0)
        inprocess_enabled = bool(self.config.get("INPROCESS_JOB_WORKERS_ENABLED"))

        if backend == "inprocess" and workers == 0:
            return [
                RuntimeDiagnostic(
                    id="queue_workers_disabled",
                    severity="warning" if pending else "info",
                    title="Queue workers are not running",
                    evidence={"backend": backend, "workers": workers, "pending": pending, "inprocess_workers_enabled": inprocess_enabled},
                    impact="New workflows can remain queued until a worker starts.",
                    recommended_action="Start in-process workers or run full-stack Celery workers for autonomous execution.",
                    auto_repairable=True,
                    tags=["queue", "workflow"],
                )
            ]
        return []

    def _redis_unavailable(self) -> Iterable[RuntimeDiagnostic]:
        if not self.config.get("REDIS_ENABLED"):
            return []
        if self.redis_available is True:
            return []
        return [
            RuntimeDiagnostic(
                id="redis_unavailable",
                severity="error",
                title="Redis is enabled but unavailable",
                evidence={"REDIS_ENABLED": True, "redis_available": self.redis_available},
                impact="Celery and distributed runtime state can fail or silently degrade.",
                recommended_action="Start Redis or switch to local-dev/inprocess mode intentionally.",
                requires_operator_action=True,
                tags=["redis", "queue"],
            )
        ]

    def _api_redirect_noise(self) -> Iterable[RuntimeDiagnostic]:
        if _API_REDIRECT_NOISE_REPAIRED:
            return []
        return [
            RuntimeDiagnostic(
                id="api_redirect_noise",
                severity="info",
                title="Canonical API URL guard active",
                evidence={"canonical_api_suffix": "no trailing slash under /api/v1"},
                impact="Trailing-slash API calls can produce 308 redirects in the Next.js proxy.",
                recommended_action="Keep API client URLs slashless; clear stale browser cache if old calls keep appearing.",
                auto_repairable=True,
                tags=["api", "frontend"],
            )
        ]

    def _observer_write_denied(self) -> Iterable[RuntimeDiagnostic]:
        from services.auth.jwt_auth import is_dev_env

        if self.identity_role != "AUDIT_OBSERVER":
            return []
        return [
            RuntimeDiagnostic(
                id="observer_write_denied",
                severity="warning",
                title="Current role is read-only",
                evidence={"role": self.identity_role, "dev_bypass_active": is_dev_env()},
                impact="Create, approve, replay and incident resolution actions will be rejected by RBAC.",
                recommended_action="Use an OPERATOR account for write actions. Local development allows bypassing this for repairs.",
                requires_operator_action=True,
                tags=["auth", "rbac"],
            )
        ]

    def _ephemeral_workflow_enabled(self) -> Iterable[RuntimeDiagnostic]:
        if not self.config.get("EPHEMERAL_WORKFLOWS_ENABLED"):
            return []
        return [
            RuntimeDiagnostic(
                id="ephemeral_workflow_enabled",
                severity="warning",
                title="Ephemeral workflow mode enabled",
                evidence={"EPHEMERAL_WORKFLOWS_ENABLED": True},
                impact="Workflow create/list/detail/approve can split across in-memory and database stores.",
                recommended_action="Disable EPHEMERAL_WORKFLOWS_ENABLED unless running a narrow UI mock test.",
                requires_operator_action=True,
                tags=["workflow", "runtime"],
            )
        ]

    def _active_error_fingerprints(self) -> Iterable[RuntimeDiagnostic]:
        count = int(self.active_error_fingerprints.get("count") or 0)
        recurrence_total = int(self.active_error_fingerprints.get("recurrence_total") or 0)
        if count <= 0:
            return []

        signoff_only = bool(self.active_error_fingerprints.get("signoff_serialization_only"))
        return [
            RuntimeDiagnostic(
                id="active_error_fingerprints",
                severity="error" if recurrence_total >= 5 else "warning",
                title="Active learned error fingerprints",
                evidence=self.active_error_fingerprints,
                impact="The system has learned repeated backend failures that still count against the global error indicator.",
                recommended_action=(
                    "Run repair after verifying /api/v1/governance/signoffs serializes correctly."
                    if signoff_only
                    else "Inspect Learning/Fingerprints and apply the targeted fix before marking fingerprints inactive."
                ),
                auto_repairable=True if signoff_only or is_dev_env else False,
                requires_operator_action=not (signoff_only or is_dev_env),
                tags=["learning", "observability", "repair"],
            )
        ]


def diagnostics_to_dict(findings: Iterable[RuntimeDiagnostic]) -> list[dict[str, Any]]:
    return [finding.to_dict() for finding in findings]
