import asyncio
import os
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, AsyncMock

from packages.orchestration.agi.learning.specialist_forge import SpecialistForge
from packages.orchestration.agi.agent_registry import discover_and_build_specialists
from packages.persistence.models import Base, SubTask, Project, User

# Mock DB for Test
DB_URL = "sqlite+aiosqlite:///:memory:"

class MockResponse:
    def __init__(self, content):
        self.content = content

async def verify_phase_52_offline():
    print("\n[PHASE 52] OTONOM UZMAN SENTEZİ (OFFLINE MOCK) DOĞRULAMA BAŞLATILIYOR...")
    
    # 1. Mock Orchestrator Hazırla
    mock_orch = MagicMock()
    mock_orch.complete_task = AsyncMock()
    
    # Sentezlenecek uzman JSON yanıtı
    mock_json = {
        "role_id": "test_specialist_x",
        "title": "Quantum Backend Optimizer",
        "system_prompt": "Sen kuantum seviyesinde backend optimizasyonu yapan bir uzmansın.",
        "capabilities": ["quantum_loops", "hyper_scaling"]
    }
    mock_orch.complete_task.return_value = MockResponse(json.dumps(mock_json))
    
    # Forge nesnesini mock orkestratör ile başlat
    roles_path = "agents/dynamic_test_agents.json"
    if os.path.exists(roles_path): os.remove(roles_path)
    
    forge = SpecialistForge(model_orch=mock_orch, roles_path=roles_path)
    
    # 2. Mock DB Hazırla
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # 3. Başarılı bir görev deseni ekle
        user = User(email="mock@faz52.agi", hashed_password="...")
        packages.persistence.add(user)
        await packages.persistence.commit()
        
        project = Project(title="Mock Project", owner_id=user.id)
        packages.persistence.add(project)
        await packages.persistence.commit()
        
        subtask = SubTask(
            project_id=project.id,
            agent_id="backend_dev",
            prompt="Optimize queries.",
            result="Done.",
            quality_score=0.99
        )
        packages.persistence.add(subtask)
        await packages.persistence.commit()
        
        # 4. Forge İşlemini Çalıştır
        print("[*] Uzman Sentezi (Forge) çalıştırılıyor...")
        results = await forge.forge_new_specialists(db)
        
        if not results:
            print("[ERROR] Sentez sonucu boş döndü.")
            return

        print(f"[+] Sentez başarılı: {results[0].get('id')}")

    # 5. Kalıcılık Kontrolü
    if os.path.exists(roles_path):
        with open(roles_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if any(a["id"] == "test_specialist_x" for a in data):
                print("[SUCCESS] Kalıcı kayıt (Persistence) doğrulandı: agents/dynamic_test_agents.json")
            else:
                print("[ERROR] Kayıt içeriği hatalı.")
    else:
        print("[ERROR] Dosya oluşturulamadı.")

    print("\n[PHASE 52] DOĞRULAMA TAMAMLANDI.")
    if os.path.exists(roles_path): os.remove(roles_path)

if __name__ == "__main__":
    asyncio.run(verify_phase_52_offline())
