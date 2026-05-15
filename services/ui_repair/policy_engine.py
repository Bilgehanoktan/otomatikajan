import uuid
from datetime import datetime, timezone, time, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UIGovernancePolicy, UIPolicyViolation, UIPolicyOverride

class PolicyEngine:
    """Evaluates Policy-as-Code rules for autonomous operations."""
    
    @staticmethod
    async def evaluate_action(
        db: AsyncSession, 
        project_key: str, 
        operation_type: str, 
        context: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[uuid.UUID]]:
        """
        Evaluates if an action is allowed based on active policies.
        Returns (is_allowed, reason, violation_id).
        """
        # 1. Fetch relevant policies (Global + Project specific)
        stmt = select(UIGovernancePolicy).where(
            (UIGovernancePolicy.project_key.in_([project_key, "GLOBAL"])) &
            (UIGovernancePolicy.is_active == True)
        )
        policies = (await db.execute(stmt)).scalars().all()
        
        for policy in policies:
            is_violated, details = PolicyEngine._check_rule(policy, operation_type, context)
            
            if is_violated:
                # 2. Check for active overrides
                if await PolicyEngine._has_active_override(db, policy.id):
                    continue
                
                # 3. Handle violation based on severity
                violation_id = uuid.uuid4()
                decision = "BLOCKED" if policy.severity == "ENFORCE" else "WARNED"
                
                violation = UIPolicyViolation(
                    id=violation_id,
                    policy_id=policy.id,
                    project_key=project_key,
                    incident_id=context.get("incident_id"),
                    operation_type=operation_type,
                    violation_details_json={**details, "policy_name": policy.policy_name},
                    decision=decision,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(violation)
                await db.commit()
                
                if policy.severity == "ENFORCE":
                    return False, f"Policy Violation: {policy.policy_name}", violation_id
        
        return True, "Allowed", None

    @staticmethod
    def _check_rule(policy: UIGovernancePolicy, operation_type: str, context: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Internal rule evaluation logic."""
        rule = policy.rule_definition_json
        
        if policy.rule_type == "TIME_WINDOW":
            # Example: {"denied_windows": [{"start": "02:00", "end": "05:00"}]}
            now_time = datetime.now(timezone.utc).time()
            for window in rule.get("denied_windows", []):
                start = time.fromisoformat(window["start"])
                end = time.fromisoformat(window["end"])
                if start <= now_time <= end:
                    return True, {"current_time": now_time.isoformat(), "window": window}
        
        elif policy.rule_type == "SCORE_THRESHOLD":
            # Example: {"min_confidence": 0.9, "operations": ["AUTO_APPLY"]}
            if operation_type in rule.get("operations", []):
                confidence = context.get("confidence_score", 0.0)
                min_conf = rule.get("min_confidence", 0.0)
                if confidence < min_conf:
                    return True, {"confidence": confidence, "required": min_conf}
                    
        elif policy.rule_type == "ACTION_DENY":
            # Example: {"denied_operations": ["DESTRUCTIVE_CHAOS"]}
            if operation_type in rule.get("denied_operations", []):
                return True, {"operation": operation_type}
        
        return False, {}

    @staticmethod
    async def _has_active_override(db: AsyncSession, policy_id: uuid.UUID) -> bool:
        """Checks if there is a valid manual override for this policy."""
        # Simple implementation: check if any override was created in the last N minutes for a violation of this policy
        # In a real scenario, we'd link overrides to specific windows or criteria.
        stmt = select(UIPolicyOverride).join(UIPolicyViolation).where(
            UIPolicyViolation.policy_id == policy_id
        ).order_by(UIPolicyOverride.created_at.desc()).limit(1)
        
        override = (await db.execute(stmt)).scalar_one_or_none()
        if override:
            expiry = override.created_at + timedelta(minutes=override.override_duration_minutes)
            if datetime.now(timezone.utc) < expiry:
                return True
        return False
