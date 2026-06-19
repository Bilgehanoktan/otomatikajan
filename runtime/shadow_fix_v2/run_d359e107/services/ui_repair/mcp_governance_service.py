import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from libs.db.models.ui_repair_models import UIMCPServer, ProviderStatus, ToolDecision
from services.ui_repair.tool_call_policy_engine import ToolCallPolicyEngine

class MCPGovernanceService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.policy_engine = ToolCallPolicyEngine(db_session)

    async def register_server(self, server_data: Dict[str, Any]) -> UIMCPServer:
        server = UIMCPServer(
            id=uuid.uuid4(),
            server_key=server_data["server_key"],
            server_name=server_data["server_name"],
            endpoint=server_data["endpoint"],
            transport_type=server_data.get("transport_type", "stdio"),
            enabled=server_data.get("enabled", True),
            tenant_scope_json=server_data.get("tenant_scope_json", []),
            allowed_tools_json=server_data.get("allowed_tools_json", []),
            blocked_tools_json=server_data.get("blocked_tools_json", []),
            auth_mode=server_data.get("auth_mode", "NONE"),
            risk_level=server_data.get("risk_level", "MEDIUM"),
            health_status=ProviderStatus.UNKNOWN,
            created_at=datetime.now(timezone.utc)
        )
        self.db_session.add(server)
        await self.db_session.commit()
        return server

    async def get_server(self, server_key: str) -> Optional[UIMCPServer]:
        result = await self.db_session.execute(
            select(UIMCPServer).where(UIMCPServer.server_key == server_key)
        )
        return result.scalars().first()

    async def evaluate_mcp_call(
        self,
        server_key: str,
        tool_name: str,
        tenant_key: str,
        project_key: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluates an MCP tool call against server-specific governance."""
        server = await self.get_server(server_key)
        if not server:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"MCP Server '{server_key}' is not registered.",
                "risk_level": "HIGH"
            }

        if not server.enabled:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"MCP Server '{server_key}' is disabled.",
                "risk_level": server.risk_level
            }

        # Check server-level tool allow/block lists
        if server.allowed_tools_json and tool_name not in server.allowed_tools_json:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"Tool '{tool_name}' is not in the allowed list for MCP server '{server_key}'.",
                "risk_level": "HIGH"
            }
        
        if server.blocked_tools_json and tool_name in server.blocked_tools_json:
            return {
                "decision": ToolDecision.DENY,
                "reason": f"Tool '{tool_name}' is explicitly blocked for MCP server '{server_key}'.",
                "risk_level": "HIGH"
            }

        # Delegating to general policy engine for action-specific checks (e.g., write detection)
        # Note: MCP tool calls often use the tool name as the action type
        return await self.policy_engine.evaluate_call(
            tool_key=f"mcp_{server_key}", 
            tenant_key=tenant_key,
            project_key=project_key,
            action_type=tool_name,
            input_data=arguments
        )

    async def update_health(self, server_key: str, status: ProviderStatus):
        await self.db_session.execute(
            update(UIMCPServer)
            .where(UIMCPServer.server_key == server_key)
            .values(health_status=status, last_checked_at=datetime.now(timezone.utc))
        )
        await self.db_session.commit()
