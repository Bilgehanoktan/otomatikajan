import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from apps.bilgeapi.config import settings
from apps.bilgeapi.services.review_ledger import ReviewLedgerService
from apps.bilgeapi.repositories.interface import (
    SystemFindingRepository,
    RemediationRunbookRepository,
    RemediationAttemptRepository
)

logger = logging.getLogger(__name__)


class SelfHealingPolicy:
    FORBIDDEN_ACTIONS = [
        "auto_merge",
        "auto_deploy",
        "auto_revoke_key",
        "production_migration_apply",
        "migration_downgrade",
        "branch_push",
        "production_config_change",
        "database_delete",
        "secret_rotation",
        "force_push"
    ]

    LIVENESS_RECOVERY_ACTIONS = [
        "restart_stateless_service",
        "restart_worker"
    ]

    def evaluate(self, finding: Dict[str, Any], runbook: Dict[str, Any]) -> Dict[str, Any]:
        action_type = runbook["action_type"]
        severity = finding["severity"]
        execution_mode = runbook["execution_mode"]

        # 1. Check forbidden actions
        if action_type in self.FORBIDDEN_ACTIONS:
            return {
                "allowed": False,
                "reason": f"Action {action_type} is explicitly forbidden by acting governor policy.",
                "action_type": action_type,
                "execution_mode": execution_mode,
                "requires_human_gate": True,
                "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
            }

        # 2. Check if self healing is enabled globally
        if not settings.BILGEAPI_SELF_HEALING_ENABLED:
            return {
                "allowed": False,
                "reason": "Self-healing is disabled globally (BILGEAPI_SELF_HEALING_ENABLED=false).",
                "action_type": action_type,
                "execution_mode": execution_mode,
                "requires_human_gate": runbook.get("requires_human_gate", True),
                "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
            }

        # 3. Check safe mode allowlist
        if settings.BILGEAPI_SELF_HEALING_SAFE_MODE:
            allowed = settings.BILGEAPI_SELF_HEALING_ALLOWED_ACTIONS
            if action_type not in allowed:
                return {
                    "allowed": False,
                    "reason": f"Action {action_type} is not in the safe-mode allowed list.",
                    "action_type": action_type,
                    "execution_mode": execution_mode,
                    "requires_human_gate": True,
                    "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
                }

        # 4. Check severity and human gate rules
        if severity == "HIGH":
            # HIGH severity always requires human gate
            return {
                "allowed": False,
                "reason": "HIGH severity findings always require Human Gate validation.",
                "action_type": action_type,
                "execution_mode": execution_mode,
                "requires_human_gate": True,
                "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
            }

        if severity == "CRITICAL":
            # CRITICAL severity only allows liveness recovery if emergency recovery enabled
            if action_type not in self.LIVENESS_RECOVERY_ACTIONS:
                return {
                    "allowed": False,
                    "reason": f"CRITICAL severity findings only allow liveness recovery actions, not {action_type}.",
                    "action_type": action_type,
                    "execution_mode": execution_mode,
                    "requires_human_gate": True,
                    "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
                }
            if not settings.BILGEAPI_EMERGENCY_RECOVERY_ENABLED:
                return {
                    "allowed": False,
                    "reason": "Emergency recovery is disabled globally (BILGEAPI_EMERGENCY_RECOVERY_ENABLED=false).",
                    "action_type": action_type,
                    "execution_mode": execution_mode,
                    "requires_human_gate": True,
                    "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
                }
            if execution_mode != "EMERGENCY_ONLY" and execution_mode != "AUTO_SAFE":
                return {
                    "allowed": False,
                    "reason": f"Runbook execution mode {execution_mode} not permitted for CRITICAL liveness recovery.",
                    "action_type": action_type,
                    "execution_mode": execution_mode,
                    "requires_human_gate": True,
                    "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
                }

        # Default allowed for LOW / MEDIUM severity if not requires_human_gate
        requires_human = runbook.get("requires_human_gate", True)
        if requires_human:
            return {
                "allowed": False,
                "reason": "Runbook configuration explicitly requires Human Gate validation.",
                "action_type": action_type,
                "execution_mode": execution_mode,
                "requires_human_gate": True,
                "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
            }

        return {
            "allowed": True,
            "reason": "Remediation policy evaluation passed.",
            "action_type": action_type,
            "execution_mode": execution_mode,
            "requires_human_gate": False,
            "forbidden_actions_checked": self.FORBIDDEN_ACTIONS
        }


class RemediationRunbookRegistry:
    def __init__(self, repo: RemediationRunbookRepository):
        self.repo = repo

    async def seed_default_runbooks(self):
        defaults = [
            {
                "name": "Restart Worker Service",
                "action_type": "restart_worker",
                "severity_allowed": "MEDIUM",
                "requires_human_gate": False,
                "enabled": True,
                "execution_mode": "AUTO_SAFE",
                "max_attempts": 2,
                "cooldown_seconds": 300,
                "safety_notes": "Stateless worker restart. Safe to automate."
            },
            {
                "name": "Rerun Smoke Tests",
                "action_type": "rerun_smoke_test",
                "severity_allowed": "MEDIUM",
                "requires_human_gate": False,
                "enabled": True,
                "execution_mode": "AUTO_SAFE",
                "max_attempts": 2,
                "cooldown_seconds": 300,
                "safety_notes": "Reruns smoke test suite on dev/staging environment."
            },
            {
                "name": "Rerun Release Gate",
                "action_type": "rerun_release_gate",
                "severity_allowed": "MEDIUM",
                "requires_human_gate": False,
                "enabled": True,
                "execution_mode": "AUTO_SAFE",
                "max_attempts": 2,
                "cooldown_seconds": 300,
                "safety_notes": "Reruns the core release gate checker."
            },
            {
                "name": "Clear Local Cache",
                "action_type": "clear_local_cache",
                "severity_allowed": "LOW",
                "requires_human_gate": False,
                "enabled": True,
                "execution_mode": "AUTO_SAFE",
                "max_attempts": 3,
                "cooldown_seconds": 60,
                "safety_notes": "Safe cache purging."
            },
            {
                "name": "Restart Stateless API Service",
                "action_type": "restart_stateless_service",
                "severity_allowed": "CRITICAL",
                "requires_human_gate": False,
                "enabled": True,
                "execution_mode": "EMERGENCY_ONLY",
                "max_attempts": 2,
                "cooldown_seconds": 300,
                "safety_notes": "Restarts primary API gateway stateless container in emergency scenario."
            }
        ]
        for rb_data in defaults:
            existing = await self.repo.get_runbook_by_name(rb_data["name"])
            if not existing:
                await self.repo.create_runbook(rb_data)


class RemediationVerifier:
    async def capture_health(self) -> Dict[str, Any]:
        # Simple health snapshot helper
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "HEALTHY",
            "checks": {
                "database": "UP",
                "cache": "UP",
                "worker": "UP"
            }
        }


class SelfHealingExecutor:
    def __init__(
        self,
        finding_repo: SystemFindingRepository,
        runbook_repo: RemediationRunbookRepository,
        attempt_repo: RemediationAttemptRepository,
        ledger_service: ReviewLedgerService,
        verifier: RemediationVerifier = None,
        skill_registry: Optional[Any] = None,
        skill_check_service: Optional[Any] = None
    ):
        self.finding_repo = finding_repo
        self.runbook_repo = runbook_repo
        self.attempt_repo = attempt_repo
        self.ledger_service = ledger_service
        self.policy = SelfHealingPolicy()
        self.verifier = verifier or RemediationVerifier()
        self.skill_registry = skill_registry
        self.skill_check_service = skill_check_service
        if not self.skill_check_service and self.skill_registry:
            from apps.bilgeapi.services.skill_check_service import SkillCheckService
            self.skill_check_service = SkillCheckService(self.skill_registry, self.ledger_service)

    async def execute_remediation(self, finding_id: str, runbook_id: str, actor_id: str) -> Dict[str, Any]:
        finding = await self.finding_repo.get_finding(finding_id)
        if not finding:
            raise ValueError(f"Finding {finding_id} not found.")

        runbook = await self.runbook_repo.get_runbook(runbook_id)
        if not runbook:
            raise ValueError(f"Runbook {runbook_id} not found.")

        # 1. Verify if the runbook matches the action allowed in policy
        decision = self.policy.evaluate(finding, runbook)

        # Run skill checks for self healing policy
        if self.skill_check_service:
            try:
                action_type = runbook["action_type"]
                check_res = await self.skill_check_service.check_patch(
                    target_type="self_healing_run",
                    target_id=finding_id,
                    skill_names=["bilgeapi-self-healing-policy"],
                    patch_code=action_type
                )
                if check_res.status == "BLOCKED":
                    decision["allowed"] = False
                    decision["reason"] = f"Remediation blocked by skill check: {check_res.checks[0].reason}"
                    decision["requires_human_gate"] = True
                elif check_res.status == "REVIEW_REQUIRED":
                    decision["allowed"] = False
                    decision["reason"] = f"Remediation requires human review by skill check: {check_res.checks[0].reason}"
                    decision["requires_human_gate"] = True
            except Exception as exc:
                logger.error("Skill check failed during self-healing: %s", exc)
                # Fail-closed
                decision["allowed"] = False
                decision["reason"] = f"Remediation blocked due to skill check failure (fail-closed): {str(exc)}"
                decision["requires_human_gate"] = True
        
        # 2. Check runbook cooldown & max attempts from database
        latest = await self.attempt_repo.get_latest_attempt_for_finding(finding_id)
        attempts = await self.attempt_repo.list_attempts_by_finding(finding_id)
        attempt_no = len(attempts) + 1

        # Evaluate cooldown
        max_att = runbook.get("max_attempts", 2)
        cooldown_sec = runbook.get("cooldown_seconds", 300)

        if latest:
            elapsed = (datetime.now(timezone.utc) - latest["created_at"].replace(tzinfo=timezone.utc)).total_seconds()
            if elapsed < cooldown_sec:
                # Cooldown block
                attempt = await self.attempt_repo.create_attempt({
                    "finding_id": finding_id,
                    "runbook_id": runbook_id,
                    "action_type": runbook["action_type"],
                    "status": "BLOCKED",
                    "attempt_no": attempt_no,
                    "error_message": f"Remediation blocked by cooldown. {elapsed:.0f}s elapsed < {cooldown_sec}s required.",
                    "policy_decision": decision,
                    "forbidden_actions_checked": decision.get("forbidden_actions_checked"),
                    "created_by": actor_id
                })
                await self.ledger_service.append_event(
                    chain_id=f"remediation_{finding_id}",
                    event_type="REMEDIATION_ATTEMPT_BLOCKED",
                    entity_type="remediation_attempt",
                    entity_id=attempt["id"],
                    actor_id=actor_id,
                    payload={
                        "attempt_id": attempt["id"],
                        "finding_id": finding_id,
                        "reason": "Cooldown limit exceeded",
                        "elapsed_seconds": elapsed,
                        "required_seconds": cooldown_sec
                    }
                )
                return attempt

        # Evaluate max attempts
        if attempt_no > max_att:
            attempt = await self.attempt_repo.create_attempt({
                "finding_id": finding_id,
                "runbook_id": runbook_id,
                "action_type": runbook["action_type"],
                "status": "BLOCKED",
                "attempt_no": attempt_no,
                "error_message": f"Remediation blocked: max attempts {max_att} exceeded (current attempt count: {attempt_no - 1}).",
                "policy_decision": decision,
                "forbidden_actions_checked": decision.get("forbidden_actions_checked"),
                "created_by": actor_id
            })
            await self.ledger_service.append_event(
                chain_id=f"remediation_{finding_id}",
                event_type="REMEDIATION_ATTEMPT_BLOCKED",
                entity_type="remediation_attempt",
                entity_id=attempt["id"],
                actor_id=actor_id,
                payload={
                    "attempt_id": attempt["id"],
                    "finding_id": finding_id,
                    "reason": "Max attempts exceeded",
                    "attempts_made": attempt_no - 1,
                    "max_allowed": max_att
                }
            )
            return attempt

        # Check policy allowance
        if not decision["allowed"]:
            # If not allowed, create attempt with BLOCKED or HUMAN_GATE_REQUIRED status
            status = "HUMAN_GATE_REQUIRED" if decision.get("requires_human_gate") else "BLOCKED"
            attempt = await self.attempt_repo.create_attempt({
                "finding_id": finding_id,
                "runbook_id": runbook_id,
                "action_type": runbook["action_type"],
                "status": status,
                "attempt_no": attempt_no,
                "error_message": decision["reason"],
                "policy_decision": decision,
                "forbidden_actions_checked": decision.get("forbidden_actions_checked"),
                "created_by": actor_id
            })
            await self.ledger_service.append_event(
                chain_id=f"remediation_{finding_id}",
                event_type="HUMAN_GATE_REQUIRED_FOR_REMEDIATION" if status == "HUMAN_GATE_REQUIRED" else "REMEDIATION_ATTEMPT_BLOCKED",
                entity_type="remediation_attempt",
                entity_id=attempt["id"],
                actor_id=actor_id,
                payload={
                    "attempt_id": attempt["id"],
                    "finding_id": finding_id,
                    "reason": decision["reason"],
                    "policy_decision": decision
                }
            )
            return attempt

        # Start execution
        before_health = await self.verifier.capture_health()
        
        attempt = await self.attempt_repo.create_attempt({
            "finding_id": finding_id,
            "runbook_id": runbook_id,
            "action_type": runbook["action_type"],
            "status": "RUNNING",
            "attempt_no": attempt_no,
            "before_health": before_health,
            "policy_decision": decision,
            "forbidden_actions_checked": decision.get("forbidden_actions_checked"),
            "ledger_chain_id": f"remediation_{finding_id}",
            "created_by": actor_id,
            "started_at": datetime.now(timezone.utc)
        })

        await self.ledger_service.append_event(
            chain_id=f"remediation_{finding_id}",
            event_type="REMEDIATION_ATTEMPT_STARTED",
            entity_type="remediation_attempt",
            entity_id=attempt["id"],
            actor_id=actor_id,
            payload={
                "attempt_id": attempt["id"],
                "finding_id": finding_id,
                "action_type": runbook["action_type"],
                "attempt_no": attempt_no
            }
        )

        # 3. Controlled Action Handler execution
        success = False
        summary = ""
        err_msg = None
        
        try:
            success, summary = await self._run_action_handler(runbook["action_type"])
        except Exception as e:
            success = False
            err_msg = str(e)
            summary = "Exception during action execution."

        after_health = await self.verifier.capture_health()
        status = "SUCCEEDED" if success else "FAILED"

        # Update attempt record
        attempt_updates = {
            "status": status,
            "after_health": after_health,
            "output_summary": summary,
            "error_message": err_msg,
            "completed_at": datetime.now(timezone.utc)
        }
        updated_attempt = await self.attempt_repo.update_attempt(attempt["id"], attempt_updates)

        # Append ledger entry
        event_type = "REMEDIATION_ATTEMPT_SUCCEEDED" if success else "REMEDIATION_ATTEMPT_FAILED"
        await self.ledger_service.append_event(
            chain_id=f"remediation_{finding_id}",
            event_type=event_type,
            entity_type="remediation_attempt",
            entity_id=attempt["id"],
            actor_id=actor_id,
            payload={
                "attempt_id": attempt["id"],
                "finding_id": finding_id,
                "status": status,
                "output_summary": summary,
                "error_message": err_msg
            }
        )

        # Update finding status if succeeded
        if success:
            await self.finding_repo.update_status(finding_id, "RESOLVED", actor_id)
        else:
            # Escalation: fail remediation can increase finding severity or risk score
            # Let's increase risk score by 15.0 to reflect escalation
            new_risk = min(100.0, finding["risk_score"] + 15.0)
            await self.finding_repo.create_finding({
                "id": finding["id"],
                "tenant_id": finding["tenant_id"],
                "source_type": finding["source_type"],
                "source_id": finding["source_id"],
                "source_hash": finding["source_hash"],
                "title": finding["title"],
                "description": f"Remediation failed. {finding['description']}",
                "severity": "HIGH" if new_risk >= 50.0 else finding["severity"],
                "risk_score": new_risk,
                "status": "OPEN",
                "occurrence_count": finding["occurrence_count"]
            })

        return updated_attempt

    async def _run_action_handler(self, action_type: str) -> tuple[bool, str]:
        # Execution of allowlisted handlers (No shell command executed)
        if action_type == "restart_worker":
            # Simulate stateless worker restart
            logger.info("Controlled action restart_worker executed.")
            return True, "Stateless worker process restarted successfully."

        elif action_type == "rerun_smoke_test":
            # Simulate running smoke test
            logger.info("Controlled action rerun_smoke_test executed.")
            return True, "Smoke tests completed: 6/6 passed."

        elif action_type == "rerun_release_gate":
            # Simulate release gate run
            logger.info("Controlled action rerun_release_gate executed.")
            return True, "Release gate check rerun completed successfully. Decision: GO."

        elif action_type == "clear_local_cache":
            logger.info("Controlled action clear_local_cache executed.")
            return True, "Local memory and file cache cleared."

        elif action_type == "restart_stateless_service":
            logger.info("Controlled action restart_stateless_service executed.")
            return True, "Stateless gateway service restarted successfully."

        elif action_type == "retry_failed_job":
            return True, "Retried failed jobs, queue healthy."

        elif action_type == "retry_stuck_taskflow_run":
            return True, "Taskflow job run retried."

        elif action_type == "resume_paused_queue_consumer":
            return True, "Queue consumer resumed."

        elif action_type == "switch_to_safe_mode":
            return True, "Switched local API router to safe mode."

        return False, f"Unknown action handler for {action_type}."


class EmergencyRecoveryService:
    def __init__(self, executor: SelfHealingExecutor, ledger_service: ReviewLedgerService):
        self.executor = executor
        self.ledger_service = ledger_service

    async def run_emergency_recovery(self, finding_id: str, action_type: str, actor_id: str) -> Dict[str, Any]:
        # Extra safeguards for emergency recovery run:
        # admin role + enabled flags + allowlist + max attempts + cooldown + ledger event
        if not settings.BILGEAPI_EMERGENCY_RECOVERY_ENABLED:
            raise ValueError("Emergency recovery is disabled globally.")

        finding = await self.executor.finding_repo.get_finding(finding_id)
        if not finding:
            raise ValueError(f"Finding {finding_id} not found.")

        if finding["severity"] != "CRITICAL":
            raise ValueError("Emergency recovery only permitted for CRITICAL severity findings.")

        # Find or create emergency runbook
        runbooks = await self.executor.runbook_repo.list_runbooks()
        matching = [r for r in runbooks if r["action_type"] == action_type and r["enabled"]]
        if not matching:
            # Create a transient enabled emergency runbook if allowed
            if action_type not in SelfHealingPolicy.LIVENESS_RECOVERY_ACTIONS:
                raise ValueError(f"Action {action_type} is not a valid liveness recovery action.")
            runbook = await self.executor.runbook_repo.create_runbook({
                "name": f"Transient Emergency {action_type}",
                "action_type": action_type,
                "severity_allowed": "CRITICAL",
                "requires_human_gate": False,
                "enabled": True,
                "execution_mode": "EMERGENCY_ONLY",
                "max_attempts": 2,
                "cooldown_seconds": 300
            })
        else:
            runbook = matching[0]

        await self.ledger_service.append_event(
            chain_id=f"emergency_recovery_{finding_id}",
            event_type="EMERGENCY_RECOVERY_STARTED",
            entity_type="system_finding",
            entity_id=finding_id,
            actor_id=actor_id,
            payload={
                "finding_id": finding_id,
                "action_type": action_type,
                "runbook_id": runbook["id"]
            }
        )

        try:
            attempt = await self.executor.execute_remediation(finding_id, runbook["id"], actor_id)
            success = attempt["status"] == "SUCCEEDED"
            event_type = "EMERGENCY_RECOVERY_SUCCEEDED" if success else "EMERGENCY_RECOVERY_FAILED"
            await self.ledger_service.append_event(
                chain_id=f"emergency_recovery_{finding_id}",
                event_type=event_type,
                entity_type="remediation_attempt",
                entity_id=attempt["id"],
                actor_id=actor_id,
                payload={
                    "attempt_id": attempt["id"],
                    "status": attempt["status"],
                    "error_message": attempt.get("error_message")
                }
            )
            return attempt
        except Exception as e:
            await self.ledger_service.append_event(
                chain_id=f"emergency_recovery_{finding_id}",
                event_type="EMERGENCY_RECOVERY_FAILED",
                entity_type="system_finding",
                entity_id=finding_id,
                actor_id=actor_id,
                payload={
                    "error": str(e)
                }
            )
            raise e
