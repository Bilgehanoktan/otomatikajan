import asyncio
import os
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.agi.cognitive.evolution_engine import evolution_engine
from agents.agent_registry import discover_and_build_specialists
from db.models import Base, SubTask, Project, User

# Mock DB for Test
DB_URL = "sqlite+aiosqlite:///:memory:"

async def verify_phase_52():
    print("\n[PHASE 52] OTONOM UZMAN SENTEZİ (SPECIALIST FORGE) DOĞRULAMA BAŞLATILIYOR...")
    
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # 1. Mock Veri Hazırla (Başarılı bir desen)
        user = User(email="test@faz52.agi", hashed_password="...")
        db.add(user)
        await db.commit()
        
        project = Project(title="Test Project 52", owner_id=user.id)
        db.add(project)
        await db.commit()
        
        # Specialist Forge >= 0.9 skorlu görevlere bakar
        subtask = SubTask(
            project_id=project.id,
            agent_id="backend_dev",
            prompt="Optimize high-concurrency database connections for AGI workloads.",
            result="Implemented async pool with 0.99 reliability score.",
            status="COMPLETED",
            quality_score=0.98,
            completed_at=datetime.now(timezone.utc)
        )
        db.add(subtask)
        await db.commit()
        
        print("[+] Mock başarılı görev deseni oluşturuldu (Score: 0.98).")

        # 2. Forge Döngüsünü Çalıştır
        # Not: Mock LLM yanıtı gerekecek veya gerçek LLM'e gidecek. 
        # Test ortamında ModelOrchestrator genellikle mocklanır veya gerçek API kullanır.
        print("[*] Uzman Sentezi (Forge Cycle) tetikleniyor...")
        await evolution_engine.run_specialist_forge_cycle(db)

    # 3. Kalıcılık Kontrolü (Persistence Check)
    roles_path = "agents/dynamic_agents.json"
    if os.path.exists(roles_path):
        with open(roles_path, "r", encoding="utf-8") as f:
            dynamic_agents = json.load(f)
            print(f"[+] Kalıcı hafıza doğrulandı: {len(dynamic_agents)} otonom ajan kayıtlı.")
            
            # 4. Registry Yükleme Kontrolü
            specialists = discover_and_build_specialists()
            found = False
            for aid in specialists:
                if "auto_specialist" in aid or "specialist" in aid:
                    print(f"[SUCCESS] Ajan Kayıt Defteri yeni uzmanı tanıdı: {aid}")
                    found = True
                    break
            
            if not found:
                print("[ERROR] Yeni uzman registry tarafından yüklenemedi.")
    else:
        print("[ERROR] dynamic_agents.json dosyası oluşturulamadı.")

if __name__ == "__main__":
    asyncio.run(verify_phase_52())
