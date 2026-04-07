
import asyncio
import uuid
from packages.persistence.session import AsyncSessionLocal
from packages.persistence.repositories.repository import ProjectRepository
from packages.orchestration.improvement.gate import packages.improvement_enginement_gate
from packages.orchestration.improvement.observer import observer
from packages.orchestration.orchestrator import orchestrator

async def test_improvement_system():
    print("--- 1. Proje Hataları Mocklama ---")
    async with AsyncSessionLocal() as db:
        # Test için hata durumunda bir proje ekleyelim (eğer yoksa)
        test_project = await ProjectRepository.create(
            db,
            title="Test Failure Project",
            description="A project designed to fail for observer test",
            status="error"
        )
        await ProjectRepository.set_error(db, test_project.id, "Connection timeout to LLM provider")
        await packages.persistence.commit()
        print(f"Mock proje oluşturuldu: {test_project.id}")

    print("\n--- 2. ImprovementGate Manuel Tetikleme ---")
    # Orkestratörü başlat (LLM ve model_orch için gerekli olabilir)
    if not orchestrator._is_running:
        await orchestrator.start()
        
    # Öneriyi manuel tetikle
    await improvement_gate.run_cycle()
    
    proposals = await improvement_gate.get_proposals()
    print(f"Aktif Öneri Sayısı: {len(proposals)}")
    
    for i, p in enumerate(proposals):
        print(f"\nÖneri #{i+1}:")
        print(f"Sorun: {p['issue']['reason']}")
        print(f"Yama (Patch): {p['patch'][:200]}...")
        print(f"Durum: {p['status']}")

    if not proposals:
        print("\n[UYARI] Hiç öneri üretilmedi. Bu durum LLM yanıt vermediğinde veya observer hatayı yakalayamadığında olabilir.")
        # Observer'ı direkt test et
        issues = await observer.scan_for_issues()
        print(f"Observer tarafından tespit edilen sorun sayısı: {len(issues)}")
        for issue in issues:
            print(f"- {issue['reason']}")

if __name__ == "__main__":
    asyncio.run(test_improvement_system())
