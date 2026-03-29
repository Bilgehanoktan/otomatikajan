import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import os
import json

# Mocking modules before imports that might fail
import sys
from types import ModuleType

class MockDB(ModuleType):
    def __init__(self, name):
        super().__init__(name)
    AsyncSessionLocal = MagicMock()

# core/orchestrator.py, llm/model_orchestrator.py vb. importlar için PYTHONPATH ayarı
sys.path.append(os.getcwd())

async def test_standalone_logic():
    print("--- STANDALONE VERIFICATION START ---")
    
    # 1. Test Budget Logic (ModelOrchestrator)
    from llm.model_orchestrator import ModelOrchestrator
    mo = ModelOrchestrator()
    
    # Mock Database and Project
    mock_project = MagicMock()
    mock_project.budget_limit = 0.05
    mock_project.total_cost = 0.06 # Limit aşılmış
    
    mock_db = AsyncMock()
    mock_db.get.return_value = mock_project
    
    print("[TEST 1] Butce asimi kontrol ediliyor...")
    try:
        # complete_task içindeki db.get ve limit kontrolünü tetikle
        with patch("llm.model_orchestrator.AsyncSessionLocal", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_db))):
            await mo.complete_task(
                agent_role="architect",
                prompt="test",
                system_prompt="test",
                project_id="any-uuid"
            )
        print("[FAIL] Butce asimi yakalanamadi!")
    except PermissionError as e:
        print(f"[OK] Butce bariyeri calisiyor: {e}")
    except Exception as e:
        print(f"[ERROR] Beklenmedik hata: {e}")

    # 2. Test Specialist Factory (Dynamic Creation)
    from core.agency.factory import SpecialistFactory
    
    mock_mo = AsyncMock()
    # Mock LLM response for specialist definition
    mock_mo.generate.return_value = json.dumps({
        "name": "Metal Expert",
        "role": "Graphics Engineer",
        "emoji": "🌀",
        "system_prompt": "You are a Metal expert.",
        "category": "engineering"
    })
    
    factory = SpecialistFactory(mock_mo, "agents/agency_library")
    print("\n[TEST 2] Dinamik ajan uretimi test ediliyor...")
    
    # Mock file writing to avoid actual disk IO if preferred, but here we can let it write to dynamic/
    agent_id = "Swift-Metal-Standalone-Test"
    res = await factory.build_specialist(agent_id, "Need Metal help")
    
    if res and res["id"] == agent_id:
        print(f"[OK] Dinamik ajan verisi uretildi: {res['name']}")
        # Dosya kontrolü
        file_path = f"agents/agency_library/dynamic/{agent_id}.md"
        if os.path.exists(file_path):
            print(f"[OK] Ajan dosyasi olusturuldu: {file_path}")
            # Cleanup
            os.remove(file_path)
    else:
        print("[FAIL] Dinamik ajan uretilemedi.")

    print("\n--- STANDALONE VERIFICATION COMPLETED ---")

if __name__ == "__main__":
    asyncio.run(test_standalone_logic())
