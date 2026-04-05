import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from core.agi.consciousness.affective_core import affective_core

@pytest.mark.asyncio
async def test_emotional_memory_injection():
    """
    Korteks'e kaydedilen her anının metadata'sına o anki duygusal durumun
    eklendiğini doğrular.
    """
    # 1. Affective Core durumunu ayarla (CURIOSITY Yüksek)
    affective_core.state["curiosity"] = 0.9
    affective_core.state["internal_stress"] = 0.1
    
    mock_db = AsyncMock()
    
    # 2. Bir anı kaydet
    memory = await synaptic_cortex.save(
        db=mock_db,
        agent_id="test_agent",
        body="İlginç bir deneyim.",
        category="experiment"
    )
    
    # 3. Metadata kontrolü
    metadata = memory.metadata_
    assert "affective_context" in metadata
    assert metadata["affective_context"]["curiosity"] == 0.9
    assert metadata["affective_context"]["internal_stress"] == 0.1
    print("Emotional Memory Injection: SUCCESS")

@pytest.mark.asyncio
async def test_stress_aware_foresight():
    """
    Yüksek stres altında ForesightCortex'in risk algısının değiştiğini doğrular.
    """
    from core.agi.cognitive.foresight_cortex import foresight_cortex
    
    # 1. Düşük Stres Durumu
    affective_core.state["internal_stress"] = 0.1
    
    # Mock model response
    mock_orch = AsyncMock()
    # Düşük streste model 'huzurlu' bir simülasyon sonucu dönmeli (Prompt'a göre simüle ediyoruz)
    # Gerçek testi prompt içeriğini kontrol ederek yapacağız
    
    with patch.object(foresight_cortex.model_orch, "complete_task", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = MagicMock(content=json.dumps({
            "predicted_risks": [],
            "strategic_alignment_score": 0.9
        }))
        
        plan = {"steps": ["step1"]}
        await foresight_cortex.simulate_plan(plan)
        
        # Prompt'ta stres seviyesinin geçtiğini kontrol et
        args, kwargs = mock_complete.call_args
        prompt = kwargs.get("prompt", "")
        assert "Stres Seviyesi: 0.10" in prompt
        
    # 2. Yüksek Stres Durumu
    affective_core.state["internal_stress"] = 0.85
    with patch.object(foresight_cortex.model_orch, "complete_task", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = MagicMock(content=json.dumps({
            "predicted_risks": [{"severity": "high", "failure_mode": "stress_induced"}],
            "strategic_alignment_score": 0.4
        }))
        
        await foresight_cortex.simulate_plan(plan)
        args, kwargs = mock_complete.call_args
        prompt = kwargs.get("prompt", "")
        # Prompt'ta stresin arttığını ve uyarının eklendiğini kontrol et
        assert "Stres Seviyesi: 0.85" in prompt
        assert "Hasty Code" in prompt
        
    print("Stress-Aware Foresight Prompting: SUCCESS")

if __name__ == "__main__":
    import json
    asyncio.run(test_emotional_memory_injection())
    asyncio.run(test_stress_aware_foresight())
