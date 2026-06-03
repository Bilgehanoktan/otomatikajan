import pytest
import uuid
from unittest.mock import MagicMock, patch
from services.repair.pr_agent_adapter import PRAgentAdapter
from services.repair.pr_agent_models import PRAgentReviewResult

@pytest.mark.asyncio
async def test_pr_agent_adapter_run_action():
    adapter = PRAgentAdapter()
    msg = await adapter.run_action("https://github.com/pull/1", "describe")
    assert "triggered" in msg

@pytest.mark.asyncio
async def test_pr_agent_adapter_get_findings():
    adapter = PRAgentAdapter()
    result = await adapter.get_findings("https://github.com/pull/1", "case-123")
    assert isinstance(result, PRAgentReviewResult)
    assert result.status == "SIMULATED"
    assert len(result.findings) > 0

@pytest.mark.asyncio
async def test_pr_agent_adapter_full_cycle():
    adapter = PRAgentAdapter()
    # Mocking persist_review to avoid DB during unit test if needed, 
    # but here we want to test the logic.
    with patch.object(PRAgentAdapter, 'persist_review', return_value=None):
        result = await adapter.run_full_review_cycle("https://github.com/pull/1", "case-123")
        assert result.status == "SIMULATED"
