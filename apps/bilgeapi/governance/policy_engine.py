import fnmatch
from typing import Dict, Any, Optional
from bilgeapi.governance.risk_engine import RiskEngine


class PolicyEngine:
    """
    Policy Engine for BilgeAPI Governance.
    Decides whether file operations or command executions are allowed, denied, or require approval.
    """

    def __init__(
        self,
        permissions_cfg: Dict[str, Any],
        delete_policy_cfg: Dict[str, Any],
        task_policy_cfg: Dict[str, Any],
        risk_engine: Optional[RiskEngine] = None,
    ):
        self.permissions_cfg = permissions_cfg or {}
        self.delete_policy_cfg = delete_policy_cfg or {}
        self.task_policy_cfg = task_policy_cfg or {}
        self.risk_engine = risk_engine or RiskEngine()

    def decide_file_action(self, action: str, target_path: str) -> Dict[str, Any]:
        path_str = str(target_path).replace("\\", "/")
        del_policy = self.delete_policy_cfg.get("policy", {})

        if action.lower() == "delete":
            for pattern in del_policy.get("auto_delete", []):
                if fnmatch.fnmatch(path_str, pattern) or pattern.replace("**/", "") in path_str:
                    return {"decision": "ALLOW", "risk_level": "LOW", "reason": "Auto delete pattern"}

            for pattern in del_policy.get("forbidden", []):
                if fnmatch.fnmatch(path_str, pattern) or pattern.replace("**/", "") in path_str:
                    return {"decision": "DENY", "risk_level": "CRITICAL", "reason": "Forbidden deletion target"}

            for pattern in del_policy.get("approval_required", []):
                if fnmatch.fnmatch(path_str, pattern) or pattern.replace("**/", "") in path_str:
                    return {"decision": "APPROVAL_REQUIRED", "risk_level": "HIGH", "reason": "Deletion requires approval"}

        risk_level, score, reason = self.risk_engine.evaluate_path(path_str)

        if risk_level == "CRITICAL":
            return {"decision": "DENY", "risk_level": "CRITICAL", "reason": reason}

        if risk_level == "HIGH":
            return {"decision": "APPROVAL_REQUIRED", "risk_level": "HIGH", "reason": reason}

        perms = self.permissions_cfg.get("permissions", {})
        allowed_actions = perms.get("allow", [])
        if action in allowed_actions or "*" in allowed_actions:
            return {"decision": "ALLOW", "risk_level": risk_level, "reason": reason}

        return {"decision": "APPROVAL_REQUIRED", "risk_level": risk_level, "reason": "Action not explicitly allowed"}

    def decide_command_action(self, command: str) -> Dict[str, Any]:
        cmd_clean = command.strip().lower()
        perms = self.permissions_cfg.get("permissions", {})
        deny_list = perms.get("deny", [])

        for pattern in deny_list:
            pat_clean = pattern.replace("*", "").strip().lower()
            if pat_clean and pat_clean in cmd_clean:
                return {"decision": "DENY", "risk_level": "CRITICAL", "reason": f"Command matches deny rule: {pattern}"}

        allow_list = perms.get("allow", [])
        for pattern in allow_list:
            pat_clean = pattern.replace("*", "").strip().lower()
            if pat_clean and cmd_clean.startswith(pat_clean):
                return {"decision": "ALLOW", "risk_level": "LOW", "reason": "Command matches allow rule"}

        return {"decision": "APPROVAL_REQUIRED", "risk_level": "MEDIUM", "reason": "Command is unspecified"}
