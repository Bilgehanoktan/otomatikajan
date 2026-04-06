import asyncio
import uuid
import os
import sys

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.persistence.session import AsyncSessionLocal
from packages.persistence.models import Project, ProjectStatus
from packages.persistence.repository import ProjectRepository
from startup.lifespan import _analyze_interrupted_tasks
from packages.orchestration.agi.governance.resilience_agent import resilience_agent

async def test_resilience_flow():
    print("AGI Resilience Testi baslatiliyor...")
    
    async with AsyncSessionLocal() as db:
        # 1. Senaryo: 'RUNNING' durumunda takılı kalan bir proje oluştur (Kapanma öncesi durum)
        project_id = str(uuid.uuid4())
        p = Project(
            id=project_id,
            title="Test Resilience Project",
            description="Bu proje otonom kurtarma testidir.",
            status=ProjectStatus.RUNNING,
            execution_context={"test_mark": "persistent"}
        )
        packages.persistence.add(p)
        await packages.persistence.commit()
        print(f"Hazirlik: '{project_id}' id'li RUNNING projesi olusturuldu.")

    # 2. Adım: Lifespan restart simülasyonu (_analyze_interrupted_tasks)
    print("Sistem restart simule ediliyor (_analyze_interrupted_tasks)...")
    await _analyze_interrupted_tasks()
    
    async with AsyncSessionLocal() as db:
        # Repository.get kullan
        p_reloaded = await ProjectRepository.get(db, project_id)
        if p_reloaded and p_reloaded.status == ProjectStatus.INTERRUPTED:
            print(f"Basari: Proje durumu INTERRUPTED olarak guncellendi.")
        else:
            print(f"Hata: Proje durumu beklenen INTERRUPTED degil: {p_reloaded.status if p_reloaded else 'null'}")
            return

    # 3. Adım: Resilience Agent otonom kurtarma simülasyonu
    print("Resilience Agent taramasi baslatiliyor...")
    # Not: Agent'ın loop'unu beklemek yerine manuel scan_and_recover tetikliyoruz
    await resilience_agent.scan_and_recover()
    
    async with AsyncSessionLocal() as db:
        p_final = await ProjectRepository.get(db, project_id)
        if p_final and p_final.status == ProjectStatus.RESUMING:
            print(f"Basari: Resilience Agent projeyi RESUMING durumuna aldi.")
        else:
            print(f"Hata: Resilience Agent projeyi kurtaramadi. Durum: {p_final.status if p_final else 'null'}")
            return

    print("\nAGI Resilience Testi BASARIYLA tamamlandi.")
    print("Kanitlar veritabaninda dogrulandi.")

if __name__ == "__main__":
    asyncio.run(test_resilience_flow())
