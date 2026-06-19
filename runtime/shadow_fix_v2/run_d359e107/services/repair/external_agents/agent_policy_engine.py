import os
from pathlib import Path
from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.repair_models import AgentCapabilityModel

class AgentPolicyEngine:
    @staticmethod
    def is_subpath(child: Path, parent: Path) -> bool:
        """Helper to check if child path is strictly under parent path."""
        try:
            # Resolve to absolute paths
            resolved_child = child.resolve()
            resolved_parent = parent.resolve()
            # On Windows, drive letters must match
            if resolved_child.drive.lower() != resolved_parent.drive.lower():
                return False
            # Check prefix relationship
            return resolved_parent in resolved_child.parents or resolved_child == resolved_parent
        except Exception:
            return False

    @classmethod
    def validate_paths(
        cls, 
        target_paths: List[str], 
        workspace_root: Path, 
        allowed_dirs: List[str], 
        blocked_dirs: List[str]
    ) -> Tuple[bool, str]:
        """Validates that target paths are canonical, do not escape the workspace, and match rules."""
        abs_workspace = workspace_root.resolve()

        for path_str in target_paths:
            # Guard against absolute path or windows drive escape
            p = Path(path_str)
            
            # Resolve the path relative to workspace if it is relative
            if not p.is_absolute():
                resolved_p = (abs_workspace / p).resolve()
            else:
                resolved_p = p.resolve()

            # 1. Traversal and symlink escape verification
            if not cls.is_subpath(resolved_p, abs_workspace):
                # Check if it falls under any explicitly allowed directory outside workspace (if any)
                is_in_allowed_dir = False
                for allowed in allowed_dirs:
                    allowed_path = Path(allowed)
                    if not allowed_path.is_absolute():
                        allowed_path = (abs_workspace / allowed_path).resolve()
                    else:
                        allowed_path = allowed_path.resolve()
                    if cls.is_subpath(resolved_p, allowed_path):
                        is_in_allowed_dir = True
                        break
                if not is_in_allowed_dir:
                    return False, f"Path traversal or escape attempt detected: '{path_str}' resolves outside workspace boundary."

            # 2. Explicit Blocked Directories Check
            for blocked in blocked_dirs:
                blocked_path = Path(blocked)
                if not blocked_path.is_absolute():
                    blocked_path = (abs_workspace / blocked_path).resolve()
                else:
                    blocked_path = blocked_path.resolve()
                if cls.is_subpath(resolved_p, blocked_path):
                    return False, f"Access to directory '{path_str}' is blocked by policy."

            # 3. Explicit Allowed Directories Check (if allowed list is not empty)
            if allowed_dirs:
                in_any_allowed = False
                for allowed in allowed_dirs:
                    # If allowed is a relative path in config, check relative to workspace
                    allowed_path = Path(allowed)
                    if not allowed_path.is_absolute():
                        allowed_path = (abs_workspace / allowed_path).resolve()
                    else:
                        allowed_path = allowed_path.resolve()
                    
                    if cls.is_subpath(resolved_p, allowed_path):
                        in_any_allowed = True
                        break
                if not in_any_allowed:
                    return False, f"Access to directory '{path_str}' is not in the allowed directories list."

        return True, ""

    @classmethod
    async def validate_execution(
        cls,
        db: AsyncSession,
        agent_key: str,
        command_handler: str,
        target_paths: List[str],
        cost: float,
        workspace_root: Path,
        network_domains: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Validates if an agent is authorized to execute a specific action."""
        # Query agent capabilities
        from services.repair.external_agents.agent_capability_registry import AgentCapabilityRegistry
        capability = await AgentCapabilityRegistry.get_agent_capability(db, agent_key)
        
        if not capability:
            return False, f"Agent '{agent_key}' is not registered in the capability database."

        # 1. Enabled check
        if not capability.enabled:
            return False, f"Agent '{agent_key}' is disabled."

        # 2. Cost limit check
        if cost > capability.max_cost_limit:
            return False, f"Requested cost ({cost}) exceeds agent's max cost limit ({capability.max_cost_limit})."

        # 3. Command Handler allowlist check
        allowed_commands = capability.allowed_commands or []
        blocked_commands = capability.blocked_commands or []

        if command_handler not in allowed_commands:
            return False, f"Command handler '{command_handler}' is not allowed for agent '{agent_key}'."
            
        if command_handler in blocked_commands:
            return False, f"Command handler '{command_handler}' is blocked for agent '{agent_key}'."

        # 4. Path policy check
        allowed_dirs = capability.allowed_directories or []
        blocked_dirs = capability.blocked_directories or []
        
        paths_ok, path_err = cls.validate_paths(target_paths, workspace_root, allowed_dirs, blocked_dirs)
        if not paths_ok:
            return False, path_err

        # 5. Network policy check
        network_policy = capability.network_policy or "disabled"
        allowed_domains = capability.allowed_domains or []
        
        if network_domains:
            if network_policy == "disabled":
                return False, f"Network access is disabled for agent '{agent_key}'."
            elif network_policy == "restricted":
                for domain in network_domains:
                    if domain not in allowed_domains:
                        return False, f"Domain '{domain}' is not in the allowed domains list for agent '{agent_key}'."

        return True, ""
