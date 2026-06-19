import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

from apps.bilgeapi.config import settings, AutonomyMode
from apps.bilgeapi.repositories.interface import AutonomyDecisionRepository, IncidentRepository

logger = logging.getLogger("bilgeapi.autonomy_decision")

class IncidentClassifier:
    def classify(self, incident_data: Any) -> str:
        """
        Classifies an incident based on message, kind, stack trace and tags.
        Returns one of: DATABASE_FAILURE, API_GATEWAY_TIMEOUT, LIVENESS_PROBE_FAIL,
        SECURITY_BREACH, RESOURCE_EXHAUSTION, UNKNOWN_ANOMALY.
        """
        msg = incident_data.error_message.lower() if incident_data.error_message else ""
        stack = incident_data.stack_trace.lower() if incident_data.stack_trace else ""
        kind = incident_data.kind.lower() if incident_data.kind else ""
        tags = [t.lower() for t in incident_data.tags] if incident_data.tags else []

        # 1. Security Breach check
        sec_keywords = ["unauthorized", "credential", "auth", "permission", "token", "jwt", "secret", "forbidden", "login", "api key"]
        if any(kw in msg for kw in sec_keywords) or any(kw in stack for kw in sec_keywords) or "security" in kind or any("security" in t for t in tags):
            return "SECURITY_BREACH"

        # 2. Database Failure check
        db_keywords = ["db", "database", "postgres", "sql", "migration", "connection pool", "sqlite", "query", "deadlock"]
        if any(kw in msg for kw in db_keywords) or any(kw in stack for kw in db_keywords) or "db" in kind or any("db" in t for t in tags):
            return "DATABASE_FAILURE"

        # 3. API Gateway Timeout check
        timeout_keywords = ["timeout", "gateway", "unreachable", "504", "502", "connection refused", "bad gateway"]
        if any(kw in msg for kw in timeout_keywords) or "timeout" in kind:
            return "API_GATEWAY_TIMEOUT"

        # 4. Liveness Probe Fail check
        live_keywords = ["liveness", "healthcheck", "ping", "unhealthy", "probe"]
        if any(kw in msg for kw in live_keywords) or "liveness" in kind:
            return "LIVENESS_PROBE_FAIL"

        # 5. Resource Exhaustion check
        resource_keywords = ["disk", "memory", "out of memory", "oom", "cpu", "exhausted", "space"]
        if any(kw in msg for kw in resource_keywords) or "exhaustion" in kind:
            return "RESOURCE_EXHAUSTION"

        return "UNKNOWN_ANOMALY"


class AutonomyDecisionEngine:
    def __init__(self, decision_repo: AutonomyDecisionRepository, incident_repo: IncidentRepository):
        self.decision_repo = decision_repo
        self.incident_repo = incident_repo
        self.classifier = IncidentClassifier()

    def calculate_risk(self, incident: Any, action_type: Optional[str]) -> Tuple[float, str]:
        """
        Calculates risk score (0 to 100) and risk level (LOW, MEDIUM, HIGH, CRITICAL).
        """
        score = 0.0

        # 1. Base score by incident severity
        severity = incident.severity.upper() if hasattr(incident.severity, "upper") else str(incident.severity).upper()
        if severity == "CRITICAL":
            score += 75.0
        elif severity == "HIGH":
            score += 50.0
        elif severity == "MEDIUM":
            score += 25.0
        else: # LOW
            score += 10.0

        # 2. Environment modifier
        env = incident.environment.lower() if incident.environment else "development"
        if env == "production":
            score += 15.0
        elif env == "staging":
            score += 5.0

        # 3. Action type modifier
        if action_type:
            action = action_type.lower()
            if action in ("clear_local_cache", "health_recheck", "read-only_diagnostic"):
                score += 0.0
            elif action in ("stuck_job_cancel", "sandbox_retry", "evidence_regeneration"):
                score += 10.0
            elif action in ("container_restart", "db_migration"):
                score += 30.0
            elif action in ("production_config_change", "secret_rotation"):
                score += 50.0
            elif action in ("database_delete", "force_push", "auto_merge", "auto_deploy"):
                score += 70.0
            else:
                score += 20.0 # Default fallback modifier for unknown proposed actions

        # Bounding
        final_score = max(0.0, min(100.0, score))

        # Risk level mapping
        if final_score < 25.0:
            level = "LOW"
        elif final_score < 50.0:
            level = "MEDIUM"
        elif final_score < 75.0:
            level = "HIGH"
        else:
            level = "CRITICAL"

        return final_score, level

    async def decide(self, incident_id: str, action_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluates incident and action type to issue eligibility decision.
        Persists decision log to repository.
        """
        incident = await self.incident_repo.get(incident_id)
        if not incident:
            raise ValueError(f"Incident {incident_id} not found.")

        classification = self.classifier.classify(incident)
        risk_score, risk_level = self.calculate_risk(incident, action_type)
        active_mode = settings.BILGEAPI_AUTONOMY_MODE

        requires_human_gate = False
        human_gate_type = None

        # Autonomy mode overrides and eligibility mapping
        if active_mode == AutonomyMode.OFF:
            eligibility = "BLOCKED"
            decision_reason = "Autonomy is completely disabled (OFF)."
        elif active_mode == AutonomyMode.OBSERVE_ONLY:
            eligibility = "BLOCKED"
            decision_reason = "Observe-only mode blocks all execution actions."
        elif risk_level == "CRITICAL":
            eligibility = "BLOCKED"
            decision_reason = "CRITICAL risk level is unconditionally blocked to safeguard infrastructure."
        elif risk_level == "HIGH":
            eligibility = "HUMAN_GATE_REQUIRED"
            requires_human_gate = True
            human_gate_type = "remediation_approval"
            decision_reason = "HIGH risk actions require explicit Human Gate validation."
        elif risk_level == "MEDIUM":
            if active_mode == AutonomyMode.DIAGNOSE_ONLY:
                eligibility = "BLOCKED"
                decision_reason = "DIAGNOSE_ONLY mode restricts execution of MEDIUM risk actions."
            else:
                eligibility = "WARNING_OPERATOR_REVIEW"
                requires_human_gate = True
                human_gate_type = "operator_review"
                decision_reason = "MEDIUM risk actions allow evidence collection but require operator review prior to execution."
        else: # LOW risk
            if active_mode == AutonomyMode.DIAGNOSE_ONLY:
                # Diagnostics/safe actions are allowed in DIAGNOSE_ONLY
                if action_type and action_type.lower() in ("clear_local_cache", "health_recheck", "read-only_diagnostic"):
                    eligibility = "AUTO_RUN"
                    decision_reason = "Safe diagnostic/LOW risk action is auto-approved under DIAGNOSE_ONLY mode."
                else:
                    eligibility = "BLOCKED"
                    decision_reason = "Non-diagnostic eylemleri are blocked in DIAGNOSE_ONLY mode."
            elif active_mode in (AutonomyMode.SAFE_AUTONOMY, AutonomyMode.SUPERVISED_AUTONOMY, AutonomyMode.POLICY_BOUND_AUTONOMY):
                eligibility = "AUTO_RUN"
                decision_reason = "LOW risk action is auto-approved under safe autonomy policies."
            else:
                eligibility = "BLOCKED"
                decision_reason = "Action blocked by active autonomy mode policy."

        # Prepare payload
        decision_data = {
            "incident_id": incident_id,
            "correlation_id": incident.correlation_id or "unknown",
            "classification": classification,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "active_autonomy_mode": active_mode,
            "eligibility": eligibility,
            "action_type": action_type,
            "decision_reason": decision_reason,
            "requires_human_gate": requires_human_gate,
            "human_gate_type": human_gate_type
        }

        # Log decision to repo
        logged_decision = await self.decision_repo.create(decision_data)
        logger.info(f"Autonomy decision created: {logged_decision['decision_id']} for incident {incident_id} (Eligibility: {eligibility})")
        return logged_decision
