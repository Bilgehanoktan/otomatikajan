from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UIExternalTool, UIToolPermission, ToolDecision, 
    ToolType, ProviderStatus, UIProviderHealth
)
from services.ui_repair.external_tool_registry import ExternalToolRegistry

class ToolCallPolicyEngine:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.registry = ExternalToolRegistry(db_session)

    async def evaluate_call(
        self, 
        tool_key: str, 
        tenant_key: str, 
        project_key: str, 
        action_type: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluates a tool call against registry, scopes, and permissions."""
        
        # 1. Check Tool Registration
        tool = await self.registry.get_tool(tool_key)
        if not tool:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"Tool '{tool_key}' is not registered in the system.",
                "risk_level": "CRITICAL"
            }
        
        if not tool.enabled:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"Tool '{tool_key}' is currently disabled.",
                "risk_level": tool.risk_level
            }

        # 2. Check Provider Health
        health = await self._get_provider_health(tool.provider)
        if health and health.status == ProviderStatus.UNAVAILABLE:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"Provider '{tool.provider}' is currently UNAVAILABLE.",
                "risk_level": "HIGH"
            }

        # 3. Check Tenant & Project Scope
        if tool.tenant_scope_json and tenant_key not in tool.tenant_scope_json:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"Tenant '{tenant_key}' is not authorized to use tool '{tool_key}'.",
                "risk_level": "HIGH"
            }
        
        if tool.project_scope_json and project_key not in tool.project_scope_json:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"Project '{project_key}' is not authorized to use tool '{tool_key}'.",
                "risk_level": "MEDIUM"
            }

        # 4. Check Allowed/Blocked Actions
        if tool.blocked_actions_json and action_type in tool.blocked_actions_json:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"Action '{action_type}' is explicitly blocked for tool '{tool_key}'.",
                "risk_level": "HIGH"
            }
        
        # 5. Check Granular Permissions (Database Override)
        permission = await self._get_granular_permission(tool_key, tenant_key, project_key, action_type)
        if permission:
            return {
                "decision": permission.decision,
                "reason": permission.reason,
                "risk_level": tool.risk_level,
                "requires_approval": permission.requires_approval,
                "requires_sandbox": permission.requires_sandbox
            }

        # 6. Default Decision Based on Tool Risk and Config
        decision = ToolDecision.ALLOW
        reason = "Tool call allowed by default registry policy."
        
        if tool.requires_approval:
            decision = ToolDecision.REQUIRE_APPROVAL
            reason = "Tool is configured to require explicit operator approval."
        elif tool.requires_sandbox:
            decision = ToolDecision.REQUIRE_SANDBOX
            reason = "Tool is configured to run in a sandboxed environment."
            
        # High risk write actions on filesystem/cloud default to approval if not specified
        if tool.tool_type in [ToolType.FILE_SYSTEM, ToolType.CLOUD_API, ToolType.DATABASE] and \
           any(word in action_type.lower() for word in ["write", "delete", "update", "create"]):
            if decision == ToolDecision.ALLOW:
                decision = ToolDecision.REQUIRE_APPROVAL
                reason = "High-risk write action detected, requiring approval."

        return {
            "decision": decision,
            "reason": reason,
            "risk_level": tool.risk_level,
            "matched_policies": ["DEFAULT_REGISTRY_POLICY"]
        }

    async def _get_granular_permission(self, tool_key, tenant_key, project_key, action_type) -> Optional[UIToolPermission]:
        result = await self.db_session.execute(
            select(UIToolPermission).where(
                UIToolPermission.tool_key == tool_key,
                UIToolPermission.tenant_key == tenant_key,
                UIToolPermission.project_key == project_key,
                UIToolPermission.action_type == action_type
            )
        )
        return result.scalars().first()

    async def _get_provider_health(self, provider_name: str) -> Optional[UIProviderHealth]:
        result = await self.db_session.execute(
            select(UIProviderHealth).where(UIProviderHealth.provider == provider_name)
        )
        return result.scalars().first()
