import pytest
import uuid
from datetime import datetime, timezone
from services.ui_repair.tool_secret_guard import ToolSecretGuard
from services.ui_repair.external_tool_registry import ExternalToolRegistry
from services.ui_repair.tool_call_policy_engine import ToolCallPolicyEngine
from services.ui_repair.mcp_governance_service import MCPGovernanceService
from libs.db.models.ui_repair_models import ToolType, ToolDecision, ProviderStatus

@pytest.mark.asyncio
async def test_secret_guard_redaction():
    guard = ToolSecretGuard()
    
    # Test GitHub Token
    text = "My token is ghp_1234567890abcdef1234567890abcdef1234"
    redacted, was_redacted = guard.redact_text(text)
    assert was_redacted
    assert "[REDACTED_GITHUB_TOKEN]" in redacted
    assert "ghp_" not in redacted

    # Test Generic API Key in dict
    data = {"api_key": "some-secret-key-12345", "public": "visible"}
    redacted_data, was_redacted = guard.sanitize_data(data)
    assert was_redacted
    assert redacted_data["api_key"] == "[REDACTED_BY_KEY_NAME]"
    assert redacted_data["public"] == "visible"

@pytest.mark.asyncio
async def test_policy_engine_unknown_tool(db_session):
    engine = ToolCallPolicyEngine(db_session)
    result = await engine.evaluate_call(
        tool_key="hacker_tool",
        tenant_key="tenant_1",
        project_key="proj_1",
        action_type="exploit",
        input_data={}
    )
    assert result["decision"] == ToolDecision.DENY
    assert "not registered" in result["reason"]

@pytest.mark.asyncio
async def test_policy_engine_scope_violation(db_session):
    registry = ExternalToolRegistry(db_session)
    await registry.register_tool({
        "tool_key": "restricted_tool",
        "tool_name": "Restricted",
        "tool_type": ToolType.CUSTOM_API,
        "provider": "Internal",
        "tenant_scope_json": ["tenant_allowed"]
    })
    
    engine = ToolCallPolicyEngine(db_session)
    # Try with unauthorized tenant
    result = await engine.evaluate_call(
        tool_key="restricted_tool",
        tenant_key="tenant_hacker",
        project_key="proj_1",
        action_type="read",
        input_data={}
    )
    assert result["decision"] == ToolDecision.DENY
    assert "not authorized" in result["reason"]

@pytest.mark.asyncio
async def test_mcp_governance_write_requires_approval(db_session):
    mcp_service = MCPGovernanceService(db_session)
    await mcp_service.register_server({
        "server_key": "fs_server",
        "server_name": "Filesystem",
        "endpoint": "stdio",
        "risk_level": "HIGH"
    })
    
    registry = ExternalToolRegistry(db_session)
    await registry.register_tool({
        "tool_key": "mcp_fs_server", # policy engine uses mcp_{server_key}
        "tool_name": "MCP FS",
        "tool_type": ToolType.FILE_SYSTEM,
        "provider": "Sovereign",
        "risk_level": "HIGH"
    })

    # Call with 'write' action
    result = await mcp_service.evaluate_mcp_call(
        server_key="fs_server",
        tool_name="write_file",
        tenant_key="any",
        project_key="any",
        arguments={"path": "/etc/passwd"}
    )
    
    assert result["decision"] == ToolDecision.REQUIRE_APPROVAL
    assert "write action detected" in result["reason"].lower()

@pytest.mark.asyncio
async def test_mcp_blocked_tool(db_session):
    mcp_service = MCPGovernanceService(db_session)
    await mcp_service.register_server({
        "server_key": "secure_server",
        "server_name": "Secure",
        "endpoint": "stdio",
        "blocked_tools_json": ["delete_all"]
    })
    
    result = await mcp_service.evaluate_mcp_call(
        server_key="secure_server",
        tool_name="delete_all",
        tenant_key="any",
        project_key="any",
        arguments={}
    )
    assert result["decision"] == ToolDecision.DENY
    assert "explicitly blocked" in result["reason"]
