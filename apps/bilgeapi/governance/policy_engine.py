import re
import fnmatch
from typing import Dict, Any, List, Optional, Tuple
from apps.bilgeapi.governance.risk_engine import RiskEngine

class PolicyEngine:
    def __init__(
        self,
        permissions_cfg: Dict[str, Any],
        delete_policy_cfg: Dict[str, Any],
        task_policy_cfg: Dict[str, Any],
        risk_engine: RiskEngine
    ):
        self.permissions = permissions_cfg.get("permissions", {})
        self.delete_policy = delete_policy_cfg.get("policy", {})
        self.task_policy = task_policy_cfg.get("policy", {})
        self.risk_engine = risk_engine

    def check_path_risk(self, filepath: str) -> Tuple[str, float, str]:
        return self.risk_engine.evaluate_path(filepath)

    def decide_file_action(self, action: str, filepath: str) -> Dict[str, Any]:
        """
        Evaluates a file action (e.g. Read, Write, DeleteFile) on a target path.
        Returns a decision dictionary.
        """
        reasons = []
        
        # 1. Normalize and get path risk
        risk_level, risk_score, risk_reason = self.risk_engine.evaluate_path(filepath)
        reasons.append(f"Risk evaluation: {risk_reason}")

        # 2. Check path protection / traversal (which raises CRITICAL)
        if risk_level == "CRITICAL":
            return {
                "decision": "DENY",
                "risk_level": "CRITICAL",
                "risk_score": risk_score,
                "reasons": reasons + ["Action target path is protected or invalid"]
            }

        # 3. Check general action permission in permissions.yaml
        action_allowed = False
        action_denied = False
        action_requires_approval = False

        # Match action against allow/deny/ask (or approval_required) lists
        allow_list = self.permissions.get("allow", [])
        deny_list = self.permissions.get("deny", [])
        # Support both 'ask' and 'approval_required' keys in permissions for compatibility
        ask_list = self.permissions.get("ask", []) + self.permissions.get("approval_required", [])

        # Standardize action name matching
        action_lower = action.lower()
        if any(item.lower() == action_lower for item in deny_list):
            action_denied = True
            reasons.append(f"Action '{action}' is explicitly denied in permissions configuration")
        elif any(item.lower() == action_lower for item in allow_list):
            action_allowed = True
            reasons.append(f"Action '{action}' is explicitly allowed in permissions configuration")
        elif any(item.lower() == action_lower for item in ask_list):
            action_requires_approval = True
            reasons.append(f"Action '{action}' requires approval in permissions configuration")
        else:
            # Default fallback for unspecified action: require approval
            action_requires_approval = True
            reasons.append(f"Action '{action}' is unspecified; defaulting to approval required")

        # 4. Check delete policy specifically if action is deletion
        is_deletion = action_lower in ("delete", "deletefile", "remove", "unlink")
        if is_deletion:
            forbidden_patterns = self.delete_policy.get("forbidden", [])
            approval_patterns = self.delete_policy.get("approval_required", [])
            quarantine_patterns = self.delete_policy.get("quarantine", [])
            auto_delete_patterns = self.delete_policy.get("auto_delete", [])

            # Check forbidden
            if any(self.risk_engine._match_pattern(filepath, pat) for pat in forbidden_patterns):
                return {
                    "decision": "DENY",
                    "risk_level": "CRITICAL",
                    "risk_score": 10.0,
                    "reasons": reasons + [f"File deletion forbidden: path '{filepath}' matches forbidden patterns"]
                }
            
            # Check approval required
            if any(self.risk_engine._match_pattern(filepath, pat) for pat in approval_patterns):
                task_risk_score = max(risk_score, 7.2)
                task_risk_level = "HIGH" if task_risk_score < 8.0 else "CRITICAL"
                return {
                    "decision": "APPROVAL_REQUIRED",
                    "risk_level": task_risk_level,
                    "risk_score": task_risk_score,
                    "reasons": reasons + [f"File deletion requires approval: path '{filepath}' matches approval patterns"]
                }

            # Check quarantine
            if any(self.risk_engine._match_pattern(filepath, pat) for pat in quarantine_patterns):
                reasons.append(f"File matches quarantine pattern; deletion will be handled via quarantine")
                if risk_level in ("LOW", "MEDIUM") and not action_denied:
                    action_allowed = True
                    action_requires_approval = False
                else:
                    action_requires_approval = True

            # Check auto_delete
            if any(self.risk_engine._match_pattern(filepath, pat) for pat in auto_delete_patterns):
                reasons.append(f"File matches auto_delete pattern")
                if risk_level in ("LOW", "MEDIUM") and not action_denied:
                    action_allowed = True
                    action_requires_approval = False

        # 5. Combine action and path risk to form final decision
        decision = "ALLOW"
        if action_denied:
            decision = "DENY"
        elif action_requires_approval or risk_level in ("HIGH", "CRITICAL"):
            decision = "APPROVAL_REQUIRED"
        elif not action_allowed:
            decision = "APPROVAL_REQUIRED"

        return {
            "decision": decision,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "reasons": reasons
        }

    def decide_command_action(self, command: str) -> Dict[str, Any]:
        """
        Evaluates a command string against permissions.yaml rules.
        """
        reasons = []
        deny_patterns = self.permissions.get("deny", [])
        allow_patterns = self.permissions.get("allow", [])
        ask_patterns = self.permissions.get("ask", []) + self.permissions.get("approval_required", [])

        matched_deny = False
        matched_allow = False
        matched_ask = False

        # Command matching: checks prefix or wildcard pattern
        for pat in deny_patterns:
            if self._match_command_pattern(command, pat):
                matched_deny = True
                reasons.append(f"Command matches deny rule pattern: {pat}")
                break

        for pat in allow_patterns:
            if self._match_command_pattern(command, pat):
                matched_allow = True
                reasons.append(f"Command matches allow rule pattern: {pat}")
                break

        for pat in ask_patterns:
            if self._match_command_pattern(command, pat):
                matched_ask = True
                reasons.append(f"Command matches approval rule pattern: {pat}")
                break

        risk_score = 4.5
        risk_level = "MEDIUM"

        if matched_deny:
            decision = "DENY"
            risk_score = 9.5
            risk_level = "CRITICAL"
        elif matched_ask:
            decision = "APPROVAL_REQUIRED"
            risk_score = 7.5
            risk_level = "HIGH"
        elif matched_allow:
            decision = "ALLOW"
            risk_score = 2.0
            risk_level = "LOW"
        else:
            decision = "APPROVAL_REQUIRED"
            risk_score = 6.5
            risk_level = "HIGH"
            reasons.append("Command does not match any allow/deny rules; defaulting to approval required")

        return {
            "decision": decision,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "reasons": reasons
        }

    def decide_task_execution(self, task_risk_level: str, attempt_count: int) -> Dict[str, Any]:
        """
        Evaluates task execution properties against task_policy.yaml rules.
        """
        reasons = []
        retry_limit = self.task_policy.get("retry_limit", 3)
        low_risk_auto_execute = self.task_policy.get("low_risk_auto_execute", True)

        # 1. Check retry limit
        if attempt_count >= retry_limit:
            reasons.append(f"Task attempt count ({attempt_count}) has reached or exceeded retry limit ({retry_limit})")
            return {
                "decision": "DENY",
                "risk_level": "CRITICAL",
                "risk_score": 10.0,
                "reasons": reasons
            }

        # 2. Check task risk level
        risk_level_upper = task_risk_level.upper()
        score_map = {"LOW": 1.5, "MEDIUM": 4.5, "HIGH": 7.0, "CRITICAL": 9.0}
        risk_score = score_map.get(risk_level_upper, 4.5)

        if risk_level_upper == "LOW" and low_risk_auto_execute:
            decision = "ALLOW"
            reasons.append("Task risk level is LOW and low_risk_auto_execute is enabled")
        elif risk_level_upper in ("HIGH", "CRITICAL"):
            decision = "APPROVAL_REQUIRED"
            reasons.append(f"Task risk level is {risk_level_upper}; approval required")
        else:
            decision = "APPROVAL_REQUIRED"
            reasons.append(f"Task execution policy requires approval for risk level: {risk_level_upper}")

        return {
            "decision": decision,
            "risk_level": risk_level_upper,
            "risk_score": risk_score,
            "reasons": reasons
        }

    def _match_command_pattern(self, command: str, pattern: str) -> bool:
        cmd_clean = command.strip().lower()
        pat_clean = pattern.strip().lower()
        
        if '*' in pat_clean:
            regex_pat = fnmatch.translate(pat_clean)
            return bool(re.match(regex_pat, cmd_clean))
        else:
            return cmd_clean.startswith(pat_clean)
