import os
from pathlib import Path
from typing import Dict, Any
from apps.bilgeapi.security.path_guard import PathGuard
from apps.bilgeapi.governance.policy_engine import PolicyEngine
from apps.bilgeapi.execution.quarantine import QuarantineManager

class SafeDelete:
    def __init__(
        self,
        project_root: Path,
        workspace_dir: Path,
        quarantine_manager: QuarantineManager,
        policy_engine: PolicyEngine
    ):
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = Path(workspace_dir).resolve()
        self.quarantine_manager = quarantine_manager
        self.policy_engine = policy_engine
        self.path_guard = PathGuard(self.project_root)

    async def delete_file(self, filepath: str, db_session) -> Dict[str, Any]:
        """
        Coordinates the safe deletion of a file based on PolicyEngine rules.
        
        Medium risk files are moved to quarantine.
        High risk files raise PermissionError (wait for approval).
        Critical risk files raise ValueError (denied by default).
        
        Returns:
            Dict[str, Any]: Action summary including execution status.
        """
        # 1. Ask PolicyEngine for decision
        policy_decision = self.policy_engine.decide_file_action("Delete", filepath)
        decision = policy_decision["decision"]
        risk_level = policy_decision["risk_level"]

        # Apply constraints strictly
        if decision == "DENY" or risk_level == "CRITICAL":
            raise ValueError(f"File deletion is DENIED by policy for: {filepath}")
        
        if decision == "APPROVAL_REQUIRED" or risk_level == "HIGH":
            raise PermissionError(f"File deletion requires human approval for: {filepath}")

        # If decision is ALLOW, evaluate risk level to decide execution method
        target_path = self.path_guard.validate_and_resolve(filepath)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if risk_level == "LOW":
            # Direct delete allowed for low risk
            os.remove(target_path)
            return {
                "status": "SUCCESS",
                "action": "DIRECT_DELETE",
                "filepath": filepath,
                "risk_level": "LOW"
            }
        
        elif risk_level == "MEDIUM":
            # Medium risk must go to quarantine instead of direct deletion
            quar_item = await self.quarantine_manager.quarantine_file(
                filepath=filepath,
                reason="SafeDelete medium risk auto-quarantine",
                db_session=db_session
            )
            return {
                "status": "SUCCESS",
                "action": "QUARANTINE",
                "filepath": filepath,
                "risk_level": "MEDIUM",
                "quarantine_id": quar_item["id"]
            }
        
        else:
            raise ValueError(f"Unsupported risk level '{risk_level}' for allowed delete execution")
