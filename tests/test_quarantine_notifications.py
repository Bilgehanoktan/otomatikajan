import time
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from llm.llm_types import ProviderStats

@pytest.mark.asyncio
async def test_quarantine_event_emission():
    # Mock event_bus
    mock_emit = AsyncMock()
    with patch("core.events.event_bus.emit", mock_emit):
        # Also mock asyncio.create_task to run immediately or just capture it
        with patch("asyncio.create_task", lambda x: x): # Force synchronous for testing or just mock
            stats = ProviderStats("test_provider", "TEST_KEY", "http://test", "test-model")
            
            # Trigger failure with 429
            stats.record_failure("429 Rate Limit")
            
            # Verify emit was called with provider.quarantined
            mock_emit.assert_called()
            args, kwargs = mock_emit.call_args
            assert args[0] == "provider.quarantined"
            assert kwargs["provider"] == "test_provider"
            assert "429" in kwargs["reason"]
            assert kwargs["duration_s"] >= 900
            assert kwargs["severity"] == "warning"

@pytest.mark.asyncio
async def test_recovery_event_emission():
    # Mock event_bus
    mock_emit = AsyncMock()
    with patch("core.events.event_bus.emit", mock_emit):
        with patch("asyncio.create_task", lambda x: x):
            stats = ProviderStats("test_provider", "TEST_KEY", "http://test", "test-model")
            
            # First, quarantine it
            stats.record_failure("Generic Error")
            mock_emit.reset_mock()
            
            # Now, recover it with success
            stats.record_success(0.5)
            
            # Verify emit was called with provider.recovered
            mock_emit.assert_called()
            args, kwargs = mock_emit.call_args
            assert args[0] == "provider.recovered"
            assert kwargs["provider"] == "test_provider"
            assert kwargs["severity"] == "info"

if __name__ == "__main__":
    # Standard pytest execution
    import sys
    pytest.main([__file__])
