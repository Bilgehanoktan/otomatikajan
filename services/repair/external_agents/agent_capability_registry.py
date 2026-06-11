import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from libs.db.models.repair_models import AgentCapabilityModel

class AgentCapabilityRegistry:
    @staticmethod
    async def initialize_defaults(db: AsyncSession) -> None:
        """Seed the 7 standard agents as disabled by default with strict safety constraints."""
        defaults = [
            {
                "agent_key": "swe_agent",
                "agent_name": "SWE-agent",
                "description": "GitHub issue / failure spec -> patch candidate generation using agentic coding loop.",
                "risk_level": "high",
                "enabled": False,
                "sandbox_mode": "workspace-write",
                "requires_human_approval": True,
                "network_policy": "disabled",
                "allowed_directories": ["tests/", "services/", "apps/"],
                "blocked_directories": ["libs/db/", "configs/", "scripts/"],
                "allowed_commands": ["run_tests", "inspect_repo", "generate_patch"],
                "blocked_commands": [],
            },
            {
                "agent_key": "pr_agent",
                "agent_name": "PR-Agent",
                "description": "Pull request review, risk rating, and comment generation.",
                "risk_level": "low",
                "enabled": False,
                "sandbox_mode": "read-only",
                "requires_human_approval": True,
                "network_policy": "disabled",
                "allowed_directories": ["tests/", "services/", "apps/"],
                "blocked_directories": ["libs/db/", "configs/", "scripts/"],
                "allowed_commands": ["inspect_repo"],
                "blocked_commands": [],
            },
            {
                "agent_key": "stagehand",
                "agent_name": "Stagehand",
                "description": "UI diagnostics, browser telemetry and assertion checks.",
                "risk_level": "medium",
                "enabled": False,
                "sandbox_mode": "read-only",
                "requires_human_approval": True,
                "network_policy": "restricted",
                "allowed_domains": ["localhost", "127.0.0.1"],
                "allowed_directories": ["apps/", "tests/"],
                "blocked_directories": ["libs/", "services/"],
                "allowed_commands": ["browser_check"],
                "blocked_commands": [],
            },
            {
                "agent_key": "openhands",
                "agent_name": "OpenHands",
                "description": "Developer agent workspace execution and coding loop.",
                "risk_level": "high",
                "enabled": False,
                "sandbox_mode": "workspace-write",
                "requires_human_approval": True,
                "network_policy": "disabled",
                "allowed_directories": ["tests/", "services/", "apps/"],
                "blocked_directories": ["libs/db/", "configs/", "scripts/"],
                "allowed_commands": ["run_tests", "inspect_repo", "generate_patch"],
                "blocked_commands": [],
            },
            {
                "agent_key": "browser_agent",
                "agent_name": "Browser Agent",
                "description": "Autonomous browser agent for web-based flows and validations.",
                "risk_level": "medium",
                "enabled": False,
                "sandbox_mode": "read-only",
                "requires_human_approval": True,
                "network_policy": "restricted",
                "allowed_domains": ["localhost", "127.0.0.1"],
                "allowed_directories": ["apps/"],
                "blocked_directories": ["libs/", "services/", "configs/"],
                "allowed_commands": ["browser_check"],
                "blocked_commands": [],
            },
            {
                "agent_key": "test_gen_agent",
                "agent_name": "Test Generation Agent",
                "description": "Generates new unit and integration tests based on specs.",
                "risk_level": "medium",
                "enabled": False,
                "sandbox_mode": "workspace-write",
                "requires_human_approval": True,
                "network_policy": "disabled",
                "allowed_directories": ["tests/"],
                "blocked_directories": ["libs/db/", "configs/", "services/", "apps/"],
                "allowed_commands": ["run_tests", "generate_patch"],
                "blocked_commands": [],
            },
            {
                "agent_key": "code_review_agent",
                "agent_name": "Code Review Agent",
                "description": "Performs static code review and suggests improvements.",
                "risk_level": "low",
                "enabled": False,
                "sandbox_mode": "read-only",
                "requires_human_approval": True,
                "network_policy": "disabled",
                "allowed_directories": ["tests/", "services/", "apps/", "libs/"],
                "blocked_directories": ["configs/"],
                "allowed_commands": ["inspect_repo"],
                "blocked_commands": [],
            }
        ]

        for item in defaults:
            stmt = select(AgentCapabilityModel).where(AgentCapabilityModel.agent_key == item["agent_key"])
            res = await db.execute(stmt)
            existing = res.scalars().first()
            if not existing:
                agent = AgentCapabilityModel(
                    id=uuid.uuid4(),
                    agent_key=item["agent_key"],
                    agent_name=item["agent_name"],
                    description=item["description"],
                    risk_level=item["risk_level"],
                    enabled=item["enabled"],
                    sandbox_mode=item["sandbox_mode"],
                    requires_human_approval=item["requires_human_approval"],
                    network_policy=item["network_policy"],
                    allowed_domains=item.get("allowed_domains", []),
                    allowed_directories=item["allowed_directories"],
                    blocked_directories=item["blocked_directories"],
                    allowed_commands=item["allowed_commands"],
                    blocked_commands=item["blocked_commands"],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(agent)
        await db.commit()

    @staticmethod
    async def get_agent_capability(db: AsyncSession, agent_key: str) -> Optional[AgentCapabilityModel]:
        stmt = select(AgentCapabilityModel).where(AgentCapabilityModel.agent_key == agent_key)
        res = await db.execute(stmt)
        return res.scalars().first()
