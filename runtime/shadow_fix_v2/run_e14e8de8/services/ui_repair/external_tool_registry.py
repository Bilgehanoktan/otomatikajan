import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from libs.db.models.ui_repair_models import UIExternalTool, ToolType

class ExternalToolRegistry:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def register_tool(self, tool_data: Dict[str, Any]) -> UIExternalTool:
        tool = UIExternalTool(
            id=uuid.uuid4(),
            tool_key=tool_data["tool_key"],
            tool_name=tool_data["tool_name"],
            tool_type=tool_data["tool_type"],
            provider=tool_data["provider"],
            description=tool_data.get("description"),
            enabled=tool_data.get("enabled", True),
            risk_level=tool_data.get("risk_level", "MEDIUM"),
            tenant_scope_json=tool_data.get("tenant_scope_json", []),
            project_scope_json=tool_data.get("project_scope_json", []),
            allowed_actions_json=tool_data.get("allowed_actions_json", []),
            blocked_actions_json=tool_data.get("blocked_actions_json", []),
            requires_approval=tool_data.get("requires_approval", False),
            requires_sandbox=tool_data.get("requires_sandbox", False),
            cost_policy_json=tool_data.get("cost_policy_json", {}),
            created_at=datetime.now(timezone.utc)
        )
        self.db_session.add(tool)
        await self.db_session.commit()
        return tool

    async def get_tool(self, tool_key: str) -> Optional[UIExternalTool]:
        result = await self.db_session.execute(
            select(UIExternalTool).where(UIExternalTool.tool_key == tool_key)
        )
        return result.scalars().first()

    async def list_tools(self, enabled_only: bool = False) -> List[UIExternalTool]:
        query = select(UIExternalTool)
        if enabled_only:
            query = query.where(UIExternalTool.enabled == True)
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def initialize_default_tools(self):
        """Seed initial tools if the registry is empty."""
        existing = await self.list_tools()
        if existing:
            return

        defaults = [
            {
                "tool_key": "github_pr_tool",
                "tool_name": "GitHub PR Management",
                "tool_type": ToolType.GITHUB,
                "provider": "GitHub",
                "risk_level": "MEDIUM",
                "allowed_actions_json": ["create_pr", "comment", "list_files", "get_diff"],
                "requires_approval": True
            },
            {
                "tool_key": "playwright_tool",
                "tool_name": "Playwright Browser Automation",
                "tool_type": ToolType.BROWSER_AUTOMATION,
                "provider": "Microsoft",
                "risk_level": "LOW",
                "allowed_actions_json": ["screenshot", "click", "fill", "navigate"]
            },
            {
                "tool_key": "stagehand_tool",
                "tool_name": "Stagehand Intelligent Browser",
                "tool_type": ToolType.BROWSER_AUTOMATION,
                "provider": "Stagehand AI",
                "risk_level": "MEDIUM",
                "allowed_actions_json": ["diagnose", "act", "observe"],
                "requires_sandbox": True
            },
            {
                "tool_key": "mcp_filesystem",
                "tool_name": "MCP Local Filesystem",
                "tool_type": ToolType.FILE_SYSTEM,
                "provider": "Sovereign AGI",
                "risk_level": "HIGH",
                "allowed_actions_json": ["read_file", "write_file", "list_dir"],
                "blocked_actions_json": ["delete_recursive", "chmod_root"],
                "requires_approval": True
            }
        ]

        for data in defaults:
            await self.register_tool(data)
