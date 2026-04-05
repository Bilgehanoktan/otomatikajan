import time
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from llm.llm_types import ProviderStats, CircuitState

@pytest.mark.asyncio
async def test_quarantine_notification_flow():
    # 1. Mock Event Bus
    mock_emit = AsyncMock()
    with patch("core.events.event_bus.emit", mock_emit):
        with patch("asyncio.create_task", lambda x: x): # Sync mode for test
            stats = ProviderStats("openai", "OPENAI_API_KEY", "https://api.openai.com", "gpt-4")
            
            # 2. Trigger 429 Error
            # record_failure(error_msg) should trigger provider.quarantined
            stats.record_failure("Error 429: Rate Limit Exceeded")
            
            # Check event emission
            mock_emit.assert_called()
            last_call = mock_emit.call_args_list[-1]
            assert last_call.args[0] == "provider.quarantined"
            assert last_call.kwargs["provider"] == "openai"
            assert last_call.kwargs["duration_s"] >= 900
            
            # 3. Trigger Recovery
            mock_emit.reset_mock()
            stats.record_success(0.5)
            
            # Check recovery event
            mock_emit.assert_called()
            last_call = mock_emit.call_args_list[-1]
            assert last_call.args[0] == "provider.recovered"
            assert last_call.kwargs["provider"] == "openai"

if __name__ == "__main__":
    import sys
    pytest.main([__file__])
