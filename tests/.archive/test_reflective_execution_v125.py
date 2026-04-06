import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from packages.orchestration.agi.cognitive.sovereign_cortex import SovereignCortex
from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
from core.task_management import SubTask, ProjectTask, TaskStatus

@pytest.mark.asyncio
async def test_reflective_retry_mechanism():
    """
    Hata durumunda _diagnostic_reflection'ın tetiklendiğini ve prompt'un
    tanılama tavsiyesiyle güncellendiğini doğrular.
    """
    cortex = SovereignCortex()
    cortex.model_orch = AsyncMock()
    
    # 1. Hazırlık
    st = SubTask(id="st1", agent_id="coder", prompt="Write code")
    pt = ProjectTask(id="pt1", title="Test Project")
    
    # Mock velocity_engine failure first, then success
    mock_result_fail = MagicMock(success=False, errors=["FileNotFound: config.py"])
    mock_result_success = MagicMock(success=True, output_data="Success")
    
    # Mock diagnostic reflection response
    mock_diag_response = MagicMock(content="Dosya ağacını kontrol et ve yolu düzelt.")
    
    with patch("packages.orchestration.agi.operational.velocity_engine.velocity_engine.simulate_and_execute") as mock_exec:
        mock_exec.side_effect = [mock_result_fail, mock_result_success]
        
        with patch.object(cortex, "_diagnostic_reflection", new_callable=AsyncMock) as mock_diag:
            mock_diag.return_value = "Dosya ağacını kontrol et ve yolu düzelt."
            
            # Motivasyon ayarlarını override et (hızlı test için)
            cortex.motivation = MagicMock()
            cortex.motivation.get_persistence_multiplier.return_value = 2
            
            await cortex._execute_subtask_nexus(st, pt)
            
            # 2. Doğrulama
            assert mock_diag.called
            assert "BİLİŞSEL TANILAMA" in st.prompt
            assert "yolu düzelt" in st.prompt
            assert st.status == TaskStatus.COMPLETED
            print("Reflective Retry Mechanism: SUCCESS")

@pytest.mark.asyncio
async def test_reality_grounding_injection():
    """
    ContextBuilder'ın gerçek dünya (FS tree) bilgisini prompt'a enjekte ettiğini doğrular.
    """
    from packages.packages.memory.retrieval import context_builder
    
    context = await context_builder.build_context(
        agent_id="test",
        task_text="List files"
    )
    
    # Doğrulama: Reality context anahtar kelimeleri
    assert "Gerçeklik Bağlamı (Current FS)" in context
    assert "📂 ./" in context or "📂" in context
    print("Reality Grounding Injection: SUCCESS")

if __name__ == "__main__":
    asyncio.run(test_reflective_retry_mechanism())
    asyncio.run(test_reality_grounding_injection())
