import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.ui_repair_models import UIPolicyRule, UIPolicyDrift, UITenantProjectBinding
from libs.db.models.core_models import OperationalIncident

logger = logging.getLogger(__name__)

class PolicyDriftDetector:
    """
    Identifies deviations in cluster or project policies from global/tenant standards.
    """

    @staticmethod
    async def scan_for_drifts(db: AsyncSession, tenant_key: Optional[str] = None) -> List[UIPolicyDrift]:
        """Scans all active policies for deviations from global templates."""
        drifts = []
        
        # 1. Fetch Global Policies as templates
        global_stmt = select(UIPolicyRule).where(UIPolicyRule.scope == "GLOBAL")
        global_rules = {r.policy_key: r for r in (await db.execute(global_stmt)).scalars().all()}
        
        # 2. Fetch non-global policies
        local_stmt = select(UIPolicyRule).where(UIPolicyRule.scope != "GLOBAL")
        if tenant_key:
            local_stmt = local_stmt.where(UIPolicyRule.tenant_key == tenant_key)
            
        local_rules = (await db.execute(local_stmt)).scalars().all()
        
        for local_rule in local_rules:
            template = global_rules.get(local_rule.policy_key)
            if not template:
                continue

            # Compare definitions
            if PolicyDriftDetector._is_relaxed(local_rule, template):
                drift = UIPolicyDrift(
                    tenant_key=local_rule.tenant_key or "unknown",
                    cluster_key=local_rule.cluster_key,
                    project_key=local_rule.project_key,
                    policy_key=local_rule.policy_key,
                    drift_type="RELAXED_RESTRICTION",
                    drift_level="HIGH" if not local_rule.enabled else "MEDIUM",
                    global_definition=template.rule_definition_json,
                    local_definition=local_rule.rule_definition_json,
                    status="DETECTED"
                )
                db.add(drift)
                drifts.append(drift)
                
                # If critical drift, raise incident
                if drift.drift_level == "HIGH":
                    await PolicyDriftDetector._raise_drift_incident(db, drift)

        await db.commit()
        return drifts

    @staticmethod
    def _is_relaxed(local: UIPolicyRule, global_rule: UIPolicyRule) -> bool:
        """Determines if a local rule is less restrictive than the global rule."""
        if not local.enabled and global_rule.enabled:
            return True
        
        # Simple JSON comparison for demonstration
        # In a real system, we'd compare decision hierarchy (DENY vs ALLOW)
        local_then = local.rule_definition_json.get("then", {})
        global_then = global_rule.rule_definition_json.get("then", {})
        
        # If global rule DENIES and local rule ALLOWS or REQUIRES_APPROVAL
        if global_then.get("decision") == "DENY" and local_then.get("decision") != "DENY":
            return True
            
        return False

    @staticmethod
    async def _raise_drift_incident(db: AsyncSession, drift: UIPolicyDrift):
        """Raises an operational incident for severe policy drift."""
        incident = OperationalIncident(
            title=f"Critical Policy Drift Detected: {drift.policy_key}",
            severity="HIGH",
            component="POLICY_DRIFT_DETECTOR",
            description=(
                f"Policy drift in project {drift.project_key}. "
                f"Local policy has relaxed global security standards. Type: {drift.drift_type}"
            ),
            status="OPEN"
        )
        db.add(incident)
