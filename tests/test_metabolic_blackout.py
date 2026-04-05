import asyncio
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from llm.model_orchestrator import ModelOrchestrator
from llm.llm_types import ProviderStats, CircuitState

@pytest.mark.asyncio
async def test_metabolic_blackout_bypass():
    orchestrator = ModelOrchestrator()
    
    # 1. Tüm sağlayıcıları karantinaya al (9999 saniye sonra bitecek şekilde)
    now = time.time()
    for name, provider in orchestrator.providers.items():
        provider.quarantine_until = now + 9999
        provider.circuit = CircuitState.OPEN
    
    # 2. Event Bus ve _call metodunu mock'la
    mock_emit = AsyncMock()
    mock_call = AsyncMock()
    
    # Fake response
    from llm.llm_types import LLMResponse
    mock_call.return_value = LLMResponse(
        content="Panic Mode Response",
        input_tokens=10,
        output_tokens=10,
        model_name="test",
        provider="test",
        latency_s=0.5,
        cost_usd=0.0
    )

    with patch("core.events.event_bus.emit", mock_emit), \
         patch.object(ModelOrchestrator, "_call", mock_call):
        
        # 3. İsteği gönder
        result = await orchestrator.complete_task(
            agent_role="architect",
            prompt="Test",
            system_prompt="Test"
        )
        
        # 4. Doğrulamalar
        # - system.metabolism.blackout olayı fırlatıldı mı?
        mock_emit.assert_any_call(
            "system.metabolism.blackout",
            provider=pytest.any_str,
            agent="architect",
            message=pytest.any_str
        )
        
        # - _call metodu force_emergency=True ile çağrıldı mı?
        # Bu, blackout sonrası denemeyi temsil eder.
        last_call_kwargs = mock_call.call_args.kwargs
        assert last_call_kwargs["force_emergency"] is True
        assert result.content == "Panic Mode Response"

if __name__ == "__main__":
    import sys
    pytest.main([__file__])
