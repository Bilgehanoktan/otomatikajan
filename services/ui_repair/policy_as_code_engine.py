import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from services.ui_repair.schemas import PolicyDecision, PolicyScope, PolicyRuleType
from libs.db.models.ui_repair_models import UIPolicyRule

logger = logging.getLogger(__name__)

class PolicyAsCodeEngine:
    """
    Deterministic engine for evaluating autonomous actions against Policy-as-Code rules.
    Supports GLOBAL and PROJECT scoping with priority-based execution.
    """

    def __init__(self, rules: List[UIPolicyRule]):
        self.rules = sorted(rules, key=lambda x: (x.scope != "GLOBAL", x.priority))

    def evaluate(self, action_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates an action against the loaded policy rules.
        
        Args:
            action_type: The type of autonomous action (e.g., 'AUTO_APPLY')
            context: Execution context (project_key, risk_level, route_criticality, etc.)
            
        Returns:
            A dictionary containing the decision, reason, and matched rules.
        """
        project_key = context.get("project_key")
        matched_rules = []
        final_decision = PolicyDecision.ALLOW
        final_reason = "No restrictive policies matched."

        for rule in self.rules:
            # Scope filtering
            if rule.scope == "PROJECT" and rule.project_key != project_key:
                continue
            
            if not rule.enabled:
                continue

            # Rule matching logic (Simple deterministic JSON matching)
            if self._matches(rule, action_type, context):
                matched_rules.append(rule.policy_key)
                
                # Extract decision from rule definition
                rule_def = rule.rule_definition_json
                then_part = rule_def.get("then", {})
                rule_decision = then_part.get("decision")
                rule_reason = then_part.get("reason", "Policy match.")

                # Conflict resolution: Most restrictive wins (DENY > REQUIRE_APPROVAL > ALLOW)
                if self._is_more_restrictive(rule_decision, final_decision):
                    final_decision = rule_decision
                    final_reason = rule_reason

        return {
            "decision": final_decision,
            "reason": final_reason,
            "matched_rules": matched_rules,
            "evaluated_at": datetime.utcnow().isoformat()
        }

    def _matches(self, rule: UIPolicyRule, action_type: str, context: Dict[str, Any]) -> bool:
        """Helper to match rule 'if' conditions against context."""
        rule_def = rule.rule_definition_json
        if_part = rule_def.get("if", {})

        # Check action_type
        target_action = if_part.get("action_type")
        if target_action:
            if isinstance(target_action, list):
                if action_type not in target_action:
                    return False
            elif target_action != action_type:
                return False

        # Check other conditions in context
        for key, value in if_part.items():
            if key == "action_type":
                continue
            
            context_val = context.get(key)
            if context_val is None:
                # Special case: maintenance window checks might not be in context but boolean
                continue

            if isinstance(value, list):
                if context_val not in value:
                    return False
            elif isinstance(value, bool):
                if bool(context_val) != value:
                    return False
            elif context_val != value:
                return False

        return True

    def _is_more_restrictive(self, new_decision: str, current_decision: str) -> bool:
        """Hierarchy: DENY/BLOCKED > REQUIRE_APPROVAL > ALLOW"""
        severity = {
            PolicyDecision.DENY: 100,
            PolicyDecision.BLOCKED_BY_BUDGET: 95,
            PolicyDecision.BLOCKED_BY_COMPLIANCE: 95,
            PolicyDecision.REQUIRE_APPROVAL: 50,
            PolicyDecision.REQUIRE_MANUAL_REVIEW: 45,
            PolicyDecision.REQUIRE_MAINTENANCE_WINDOW: 40,
            PolicyDecision.ALLOW: 0,
            PolicyDecision.SIMULATION_ONLY: -1
        }
        
        return severity.get(new_decision, 0) > severity.get(current_decision, 0)
