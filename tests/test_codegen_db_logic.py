import asyncio
import os
import sys
import uuid
from unittest.mock import MagicMock

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_pure_db_persistence():
    print("--- [FAZ 12.1: SOVEREIGN CODEGEN MOCK VERİLABANI TESTİ] ---")
    
    try:
        from sovereign_codegen import CodeGenerationEngine, CodeFile, CodeLanguage
        from db.session import AsyncSessionLocal
        from db.code_repository import CodeRepository
        
        # Mock Orchestrator (LLM çağrısı yapmasın)
        mock_orch = MagicMock()
        engine = CodeGenerationEngine(mock_orch)
        
        # 1. Manuel Veri Hazırla
        test_project_id = uuid.uuid4()
        test_title = "Mock Persistence Test"
        
        print("Veritabanı kaydı oluşturuluyor...")
        async with AsyncSessionLocal() as db:
            # Önce bir CodeResult oluştur
            code_res = await CodeRepository.create_result(
                db=db,
                project_id=test_project_id,
                title=test_title,
                summary="Mock Test Summary"
            )
            
            # Dosyaları ekle
            files_data = [
                {"filename": "test.py", "path": "src/test.py", "content": "print('hello')", "language": "python"},
                {"filename": "README.md", "path": "README.md", "content": "# Test", "language": "markdown"}
            ]
            await CodeRepository.add_files(db, code_res.id, files_data)
            await db.commit()
            print(f"[OK] {len(files_data)} dosya DB'ye yazıldı.")

        # 2. Geri Yükleme Testi
        print(f"Project ID {test_project_id} geri yükleniyor...")
        restored = await engine.get_result(str(test_project_id))
        
        if restored and len(restored.files) == 2:
            print(f"[BAŞARILI] Veritabanı kalıcılığı doğrulandı.")
            print(f"  Proje: {restored.title}")
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
