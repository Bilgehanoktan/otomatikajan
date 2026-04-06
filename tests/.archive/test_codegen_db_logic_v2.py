import asyncio
import os
import sys
import uuid
from unittest.mock import MagicMock

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_pure_db_persistence():
    print("--- [FAZ 12.1: SOVEREIGN CODEGEN MOCK VERİLABANI TESTİ V2] ---")
    
    try:
        from sovereign_codegen import CodeGenerationEngine, CodeFile, CodeLanguage
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.code_repository import CodeRepository
        from packages.persistence.repository import ProjectRepository
        
        # Mock Orchestrator
        mock_orch = MagicMock()
        engine = CodeGenerationEngine(mock_orch)
        
        test_title = "Mock Persistence Test V2"
        
        print("Veritabanı kayıtları oluşturuluyor...")
        async with AsyncSessionLocal() as db:
            # 1. Önce bir Proje oluştur (FK kısıtlaması için şart)
            project = await ProjectRepository.create(
                db=db,
                title=f"[TEST] {test_title}",
                description="Test description",
                source="test"
            )
            print(f"[OK] Proje oluşturuldu: {project.id}")
            
            # 2. CodeResult oluştur
            code_res = await CodeRepository.create_result(
                db=db,
                project_id=project.id,
                title=test_title,
                summary="Mock Test Summary V2"
            )
            
            # 3. Dosyaları ekle
            files_data = [
                {"filename": "test.py", "path": "src/test.py", "content": "print('hello')", "language": "python"},
                {"filename": "README.md", "path": "README.md", "content": "# Test", "language": "markdown"}
            ]
            await CodeRepository.add_files(db, code_res.id, files_data)
            await packages.persistence.commit()
            print(f"[OK] {len(files_data)} dosya DB'ye yazıldı.")
            real_project_id = str(project.id)

        # 4. Geri Yükleme Testi
        print(f"Project ID {real_project_id} geri yükleniyor...")
        restored = await engine.get_result(real_project_id)
        
        if restored and len(restored.files) == 2:
            print(f"[BAŞARILI] Veritabanı kalıcılığı ve FK entegrasyonu doğrulandı.")
            print(f"  Proje Başlığı: {restored.title}")
            for f in restored.files:
                print(f"  - {f.path} [{f.language.value}]")
        else:
            print("[HATA] Veri geri yükleme başarısız veya eksik!")
            
    except Exception as e:
        print(f"[HATA] Beklenmedik hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pure_db_persistence())
