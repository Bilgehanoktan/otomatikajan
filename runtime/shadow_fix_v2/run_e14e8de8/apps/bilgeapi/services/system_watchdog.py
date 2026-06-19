import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apps.bilgeapi.config import settings
from apps.bilgeapi.repositories.interface import (
    ReleaseCheckRepository,
    ReviewLedgerRepository,
    SystemFindingRepository,
)
from apps.bilgeapi.services.review_ledger import PayloadRedactor, ReviewLedgerService


@dataclass
class WatchdogSignal:
    source_type: str
    source_id: str
    title: str
    description: str
    risk_points: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommended_action: Optional[str] = None
    tenant_id: Optional[str] = None
    links: Dict[str, Optional[str]] = field(default_factory=dict)


class SystemRiskScorer:
    RISK_POINTS = {
        "service_unhealthy": 40,
        "release_gate_blocker": 50,
        "ledger_invalid": 50,
        "migration_head_mismatch": 45,
        "revoked_key_usage_attempt": 35,
        "quota_abuse": 25,
        "sandbox_verification_blocked": 25,
        "ai_provider_unsafe_config": 40,
        "missing_audit_ledger_evidence": 20,
    }

    def severity_for_score(self, score: float) -> str:
        if score >= 80:
            return "CRITICAL"
        if score >= 60:
            return "HIGH"
        if score >= 30:
            return "MEDIUM"
        return "LOW"

    def score_signal(self, signal: WatchdogSignal) -> Dict[str, Any]:
        score = max(0.0, min(100.0, float(signal.risk_points)))
        return {
            "source_type": signal.source_type,
            "source_id": signal.source_id,
            "title": signal.title,
            "description": signal.description,
            "risk_score": score,
            "severity": self.severity_for_score(score),
            "evidence": signal.evidence,
            "recommended_action": signal.recommended_action,
            "tenant_id": signal.tenant_id,
            "links": signal.links,
        }


class WatchdogEvidenceBuilder:
    def __init__(self):
        self.redactor = PayloadRedactor()

    def build(self, scored_signal: Dict[str, Any]) -> Dict[str, Any]:
        return self.redactor.redact({
            "source_type": scored_signal["source_type"],
            "source_id": scored_signal["source_id"],
            "risk_score": scored_signal["risk_score"],
            "severity": scored_signal["severity"],
            "evidence": scored_signal.get("evidence") or {},
            "links": scored_signal.get("links") or {},
        })


class ActingGovernorPolicy:
    FORBIDDEN_ACTIONS = [
        "auto_merge",
        "auto_deploy",
        "auto_revoke_key",
        "production_migration_apply",
        "branch_push",
        "production_config_change",
    ]

    def recommendation_for(self, scored_signal: Dict[str, Any]) -> Dict[str, Any]:
        severity = scored_signal["severity"]
        if severity == "CRITICAL":
            action = "Require immediate human review before any remediation."
        elif severity == "HIGH":
            action = "Open operator investigation and require human gate before remediation."
        elif severity == "MEDIUM":
            action = "Acknowledge and investigate during the next operator review."
        else:
            action = "Track as informational signal."
        return {
            "recommended_action": scored_signal.get("recommended_action") or action,
            "human_gate_payload": {
                "required": severity in {"HIGH", "CRITICAL"} and settings.BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED,
                "severity": severity,
                "forbidden_actions": list(self.FORBIDDEN_ACTIONS),
            },
            "forbidden_actions": list(self.FORBIDDEN_ACTIONS),
        }


class SystemSignalCollector:
    def __init__(
        self,
        release_repo: Optional[ReleaseCheckRepository] = None,
        ledger_repo: Optional[ReviewLedgerRepository] = None,
    ):
        self.release_repo = release_repo
        self.ledger_repo = ledger_repo

    async def collect(self) -> List[WatchdogSignal]:
        signals: List[WatchdogSignal] = []
        signals.extend(await self._collect_release_gate_signals())
        signals.extend(await self._collect_ledger_signals())
        signals.extend(self._collect_config_signals())
        return signals

    async def _collect_release_gate_signals(self) -> List[WatchdogSignal]:
        if not self.release_repo:
            return []
        latest = await self.release_repo.get_latest_check()
        if not latest:
            return [WatchdogSignal(
                source_type="release_gate",
                source_id="missing-latest-check",
                title="Missing release gate evidence",
                description="No release gate check record is available for watchdog inspection.",
                risk_points=SystemRiskScorer.RISK_POINTS["missing_audit_ledger_evidence"],
                evidence={"reason": "release_check_not_found"},
                recommended_action="Run the release gate and attach evidence before final release operations.",
            )]
        blockers = latest.get("blockers") or []
        warnings = latest.get("warnings") or []
        score = float(latest.get("score") or 0.0)
        if blockers or str(latest.get("status", "")).upper() == "BLOCKED":
            return [WatchdogSignal(
                source_type="release_gate",
                source_id=str(latest.get("id") or "latest"),
                title="Release gate blocker detected",
                description="The latest release gate check contains blockers or is BLOCKED.",
                risk_points=100.0 if blockers else 80.0,
                evidence={"score": score, "status": latest.get("status"), "blocker_count": len(blockers), "warning_count": len(warnings)},
                recommended_action="Stop release activity and require operator review of blockers.",
            )]
        if warnings:
            return [WatchdogSignal(
                source_type="release_gate",
                source_id=str(latest.get("id") or "latest"),
                title="Release gate warning detected",
                description="The latest release gate check contains warnings.",
                risk_points=35.0,
                evidence={"score": score, "status": latest.get("status"), "warning_count": len(warnings)},
            )]
        return []

    async def _collect_ledger_signals(self) -> List[WatchdogSignal]:
        if not self.ledger_repo:
            return []
        recent = await self.ledger_repo.list_recent(limit=1)
        if not recent:
            return [WatchdogSignal(
                source_type="review_ledger",
                source_id="missing-recent-entry",
                title="Missing review ledger evidence",
                description="No immutable review ledger entries are available for watchdog inspection.",
                risk_points=SystemRiskScorer.RISK_POINTS["missing_audit_ledger_evidence"],
                evidence={"reason": "ledger_empty"},
                recommended_action="Generate ledger-backed evidence for critical review workflows.",
            )]
        return []

    def _collect_config_signals(self) -> List[WatchdogSignal]:
        signals: List[WatchdogSignal] = []
        if settings.BILGEAPI_AI_PATCH_PROVIDER != "mock" and not settings.BILGEAPI_ALLOW_REAL_AI_PATCH:
            signals.append(WatchdogSignal(
                source_type="config",
                source_id="ai_patch_provider",
                title="AI provider unsafe config",
                description="A real AI patch provider is selected but real AI patch execution is not explicitly allowed.",
                risk_points=SystemRiskScorer.RISK_POINTS["ai_provider_unsafe_config"] + 25,
                evidence={
                    "provider": settings.BILGEAPI_AI_PATCH_PROVIDER,
                    "allow_real": settings.BILGEAPI_ALLOW_REAL_AI_PATCH,
                },
                recommended_action="Keep provider in mock mode or explicitly review real provider enablement.",
            ))
        if settings.APP_ENV == "production" and not settings.BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED:
            signals.append(WatchdogSignal(
                source_type="config",
                source_id="watchdog_human_gate",
                title="Watchdog human gate disabled in production",
                description="Production watchdog operation requires a human gate.",
                risk_points=100.0,
                evidence={"app_env": settings.APP_ENV, "human_gate_required": False},
                recommended_action="Enable BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED before running watchdog in production.",
            ))
        return signals


class SystemFindingService:
    TERMINAL_STATUSES = {"DISMISSED", "RESOLVED"}
    VALID_TRANSITIONS = {
        "OPEN": {"ACKNOWLEDGED", "INVESTIGATING", "HUMAN_GATE_REQUIRED", "DISMISSED", "RESOLVED"},
        "ACKNOWLEDGED": {"INVESTIGATING", "HUMAN_GATE_REQUIRED", "RESOLVED", "DISMISSED"},
        "INVESTIGATING": {"HUMAN_GATE_REQUIRED", "RESOLVED", "DISMISSED"},
    }

    def __init__(
        self,
        repo: SystemFindingRepository,
        ledger_service: Optional[ReviewLedgerService] = None,
        evidence_builder: Optional[WatchdogEvidenceBuilder] = None,
        policy: Optional[ActingGovernorPolicy] = None,
    ):
        self.repo = repo
        self.ledger_service = ledger_service
        self.evidence_builder = evidence_builder or WatchdogEvidenceBuilder()
        self.policy = policy or ActingGovernorPolicy()

    @staticmethod
    def compute_source_hash(source_type: str, source_id: str, title: str, severity: str) -> str:
        payload = f"{source_type}|{source_id}|{title}|{severity}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    async def find_or_create_from_signal(
        self,
        scored_signal: Dict[str, Any],
        actor_id: str,
        correlation_id: str,
    ) -> Dict[str, Any]:
        source_hash = self.compute_source_hash(
            scored_signal["source_type"],
            scored_signal["source_id"],
            scored_signal["title"],
            scored_signal["severity"],
        )
        policy = self.policy.recommendation_for(scored_signal)
        evidence_summary = self.evidence_builder.build(scored_signal)
        existing = await self.repo.get_open_by_source_hash(source_hash)
        if existing:
            finding = await self.repo.increment_occurrence(existing["id"], evidence_summary)
            await self._append_ledger(
                event_type="SYSTEM_FINDING_DEDUPED",
                entity_id=existing["id"],
                actor_id=actor_id,
                payload={"source_hash": source_hash, "correlation_id": correlation_id},
            )
            return {"finding": finding, "created": False, "deduped": True}
        terminal = await self.repo.get_by_source_hash(source_hash)
        if terminal and terminal.get("status") in self.TERMINAL_STATUSES:
            return {"finding": terminal, "created": False, "deduped": False, "terminal": True}

        initial_status = "OPEN"
        if scored_signal["severity"] == "CRITICAL" and settings.BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED:
            initial_status = "HUMAN_GATE_REQUIRED"
        finding = await self.repo.create_finding({
            "tenant_id": scored_signal.get("tenant_id"),
            "source_type": scored_signal["source_type"],
            "source_id": scored_signal["source_id"],
            "source_hash": source_hash,
            "title": scored_signal["title"],
            "description": scored_signal["description"],
            "severity": scored_signal["severity"],
            "risk_score": scored_signal["risk_score"],
            "status": initial_status,
            "evidence_summary": evidence_summary,
            "recommended_action": policy["recommended_action"],
            "human_gate_payload": policy["human_gate_payload"],
            "bilgeapi_research_id": (scored_signal.get("links") or {}).get("research_id"),
            "bilgeapi_proposal_id": (scored_signal.get("links") or {}).get("proposal_id"),
            "bilgeapi_pr_draft_id": (scored_signal.get("links") or {}).get("pr_draft_id"),
            "bilgeapi_verification_id": (scored_signal.get("links") or {}).get("verification_id"),
            "bilgeapi_ledger_chain_id": (scored_signal.get("links") or {}).get("ledger_chain_id"),
            "created_by": actor_id,
            "correlation_id": correlation_id,
        })
        await self._append_ledger(
            event_type="SYSTEM_FINDING_CREATED",
            entity_id=finding["id"],
            actor_id=actor_id,
            payload={"source_hash": source_hash, "severity": finding["severity"], "risk_score": finding["risk_score"]},
        )
        return {"finding": finding, "created": True, "deduped": False}

    async def transition(self, finding_id: str, target_status: str, actor_id: str) -> Dict[str, Any]:
        finding = await self.repo.get_finding(finding_id)
        if not finding:
            raise ValueError("System finding not found")
        current = finding["status"]
        if current in self.TERMINAL_STATUSES:
            raise ValueError(f"System finding is terminal: {current}")
        allowed = self.VALID_TRANSITIONS.get(current, set())
        if target_status not in allowed:
            raise ValueError(f"Invalid finding transition: {current} -> {target_status}")
        updated = await self.repo.update_status(finding_id, target_status, actor_id)
        event_type = f"SYSTEM_FINDING_{target_status}"
        if target_status == "ACKNOWLEDGED":
            event_type = "SYSTEM_FINDING_ACKNOWLEDGED"
        elif target_status == "DISMISSED":
            event_type = "SYSTEM_FINDING_DISMISSED"
        await self._append_ledger(
            event_type=event_type,
            entity_id=finding_id,
            actor_id=actor_id,
            payload={"from": current, "to": target_status},
        )
        return updated

    async def acknowledge(self, finding_id: str, actor_id: str) -> Dict[str, Any]:
        return await self.transition(finding_id, "ACKNOWLEDGED", actor_id)

    async def dismiss(self, finding_id: str, actor_id: str) -> Dict[str, Any]:
        return await self.transition(finding_id, "DISMISSED", actor_id)

    async def _append_ledger(self, event_type: str, entity_id: str, actor_id: str, payload: Dict[str, Any]) -> None:
        if not self.ledger_service:
            return
        await self.ledger_service.append_event(
            chain_id="bilgeapi-watchdog",
            event_type=event_type,
            entity_type="system_finding",
            entity_id=entity_id,
            actor_id=actor_id,
            payload=payload,
        )


class SystemWatchdogService:
    def __init__(
        self,
        finding_service: SystemFindingService,
        collector: SystemSignalCollector,
        scorer: Optional[SystemRiskScorer] = None,
        ledger_service: Optional[ReviewLedgerService] = None,
        policy: Optional[ActingGovernorPolicy] = None,
    ):
        self.finding_service = finding_service
        self.collector = collector
        self.scorer = scorer or SystemRiskScorer()
        self.ledger_service = ledger_service
        self.policy = policy or ActingGovernorPolicy()
        self.last_scan_correlation_id: Optional[str] = None

    async def run_scan(self, actor_id: str) -> Dict[str, Any]:
        self._validate_runtime_policy()
        correlation_id = f"wd_{uuid.uuid4().hex[:12]}"
        self.last_scan_correlation_id = correlation_id
        await self._append_ledger("WATCHDOG_SCAN_STARTED", actor_id, {
            "correlation_id": correlation_id,
            "enabled": settings.BILGEAPI_WATCHDOG_ENABLED,
        })
        if not settings.BILGEAPI_WATCHDOG_ENABLED:
            await self._append_ledger("WATCHDOG_SCAN_COMPLETED", actor_id, {
                "correlation_id": correlation_id,
                "status": "DISABLED",
                "signals_seen": 0,
            })
            return {
                "status": "DISABLED",
                "enabled": False,
                "correlation_id": correlation_id,
                "signals_seen": 0,
                "findings_created": 0,
                "findings_deduped": 0,
                "findings": [],
                "forbidden_actions": self.policy.FORBIDDEN_ACTIONS,
                "message": "BILGEAPI_WATCHDOG_ENABLED is false; manual scan is a safe no-op.",
            }

        signals = await self.collector.collect()
        findings: List[Dict[str, Any]] = []
        created = 0
        deduped = 0
        for signal in signals:
            scored = self.scorer.score_signal(signal)
            if scored["risk_score"] < 30:
                continue
            if not settings.BILGEAPI_WATCHDOG_AUTO_FINDING:
                continue
            result = await self.finding_service.find_or_create_from_signal(scored, actor_id, correlation_id)
            findings.append(result["finding"])
            created += 1 if result["created"] else 0
            deduped += 1 if result["deduped"] else 0

        await self._append_ledger("WATCHDOG_SCAN_COMPLETED", actor_id, {
            "correlation_id": correlation_id,
            "status": "COMPLETED",
            "signals_seen": len(signals),
            "findings_created": created,
            "findings_deduped": deduped,
        })
        return {
            "status": "COMPLETED",
            "enabled": True,
            "correlation_id": correlation_id,
            "signals_seen": len(signals),
            "findings_created": created,
            "findings_deduped": deduped,
            "findings": findings,
            "forbidden_actions": self.policy.FORBIDDEN_ACTIONS,
            "message": None,
        }

    async def status(self, finding_repo: SystemFindingRepository) -> Dict[str, Any]:
        findings = await finding_repo.list_findings(limit=200)
        open_findings = [
            finding for finding in findings
            if finding.get("status") not in SystemFindingService.TERMINAL_STATUSES
        ]
        high_or_critical = [
            finding for finding in open_findings
            if finding.get("severity") in {"HIGH", "CRITICAL"}
        ]
        return {
            "enabled": settings.BILGEAPI_WATCHDOG_ENABLED,
            "status": "ENABLED" if settings.BILGEAPI_WATCHDOG_ENABLED else "DISABLED",
            "risk_threshold": settings.BILGEAPI_WATCHDOG_RISK_THRESHOLD,
            "auto_finding": settings.BILGEAPI_WATCHDOG_AUTO_FINDING,
            "human_gate_required": settings.BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED,
            "open_findings": len(open_findings),
            "high_or_critical_findings": len(high_or_critical),
            "last_scan_correlation_id": self.last_scan_correlation_id,
        }

    def _validate_runtime_policy(self) -> None:
        if settings.APP_ENV == "production" and not settings.BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED:
            raise ValueError("BILGEAPI_WATCHDOG_HUMAN_GATE_REQUIRED cannot be false in production")

    async def _append_ledger(self, event_type: str, actor_id: str, payload: Dict[str, Any]) -> None:
        if not self.ledger_service:
            return
        await self.ledger_service.append_event(
            chain_id="bilgeapi-watchdog",
            event_type=event_type,
            entity_type="watchdog_scan",
            entity_id=payload.get("correlation_id", "watchdog"),
            actor_id=actor_id,
            payload=payload,
        )
