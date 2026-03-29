import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from core.task_routing import TaskRouter

@pytest.mark.asyncio
async def test_semantic_routing_decisions():
    # Setup mock LLM
    mock_llm = AsyncMock()
    router = TaskRouter(model_orch=mock_llm)
    
    # CASE 1: Complex Plan
    mock_llm.generate.return_value = "deerflow_plan"
    res1 = await router.route_task("Mimar Tasarim", "Yeni bir proje icin mikroservis mimarisi cikar...")
    assert res1 == "deerflow_plan"
    
    # CASE 2: Research
    mock_llm.generate.return_value = "deerflow_research"
    res2 = await router.route_task("Repo Analizi", "Mevcut koddaki bagimliliklari incele...")
    assert res2 == "deerflow_research"
    
    # CASE 3: Recovery
    mock_llm.generate.return_value = "deerflow_recovery"
    res3 = await router.route_task("Sistem Hatasi", "Veritabani baglantisi koptu, acil cozum...")
    assert res3 == "deerflow_recovery"
    
    # CASE 4: Standard Project
    mock_llm.generate.return_value = "run_project"
    res4 = await router.route_task("Basit CRUD", "Kullanici listeleme ekrani yap...")
    assert res4 == "run_project"

    print("\n[SUCCESS] Semantic Task Router test decisions verified!")

if __name__ == "__main__":
    asyncio.run(test_semantic_routing_decisions())
