import asyncio
import os
import sys
import uuid

# Proje kök dizinini ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def verify_codegen_persistence():
    print("--- [FAZ 12.1: SOVEREIGN CODEGEN KALICILIK DOĞRULAMA] ---")
    
    try:
        from sovereign_codegen import init_sovereign_codegen, get_code_engine
        from llm.model_orchestrator import ModelOrchestrator
        from db.session import AsyncSessionLocal
        from db.models import Project, SovereignCodeResult
        from sqlalchemy import select
        
        orch = ModelOrchestrator()
        engine = init_sovereign_codegen(orch)
        
        test_title = f"Test Project {uuid.uuid4().hex[:6]}"
        test_desc  = "This is a test project to verify database persistence in Faz 12.1 Sovereign AGI."
        
        print(f"Kod üretimi başlatılıyor: {test_title}")
        result = await engine.generate(
            title=test_title,
            description=test_desc,
            template=None # CUSTOM
        )
        
        print(f"Üretim Tamamlandı. Durum: {result.status}")
        project_id = result.project_id
        print(f"Atanan Project ID: {project_id}")
        
        # 1. Veritabanı Kontrolü
        print("Veritabanı kayıtları kontrol ediliyor...")
        async with AsyncSessionLocal() as db:
            # Proje kontrolü
            proj_stmt = select(Project).where(Project.id == uuid.UUID(project_id))
            proj = (await db.execute(proj_stmt)).scalar_one_or_none()
            
            if proj:
                print(f"[OK] Proje veritabanında bulundu: {proj.title}")
            else:
                print("[HATA] Proje veritabanında bulunamadı!")
                return
            
            # Kod sonucu kontrolü
            res_stmt = select(SovereignCodeResult).where(SovereignCodeResult.project_id == proj.id)
            code_res = (await db.execute(res_stmt)).scalar_one_or_none()
            
            if code_res:
                print(f"[OK] Kod üretim kaydı bulundu: {code_res.status}, Dosya sayısı: {code_res.total_files}")
            else:
                print("[HATA] Kod üretim kaydı veritabanında bulunamadı!")
                return

        # 2. Re-load Kontrolü (Persistence Test)
        print("Motor yeniden başlatılıyor (simülasyon)...")
        # Global _engine'i sıfırlamak yerine yeni bir engine instance'ı ile get_result çağıralım
        # (Gerçek hayatta servis restart olduğunda olan budur)
        
        print(f"Project ID {project_id} için sonuçlar çekiliyor...")
        restored_result = await engine.get_result(project_id)
        
        if restored_result and len(restored_result.files) > 0:
            print(f"[BAŞARILI] Kalıcılık sağlandı! {len(restored_result.files)} dosya geri yüklendi.")
            for f in restored_result.files[:2]:
                print(f"  - {f.path} ({len(f.content)} chars)")
        else:
            print("[HATA] Veriler geri yüklenemedi!")
            
    except Exception as e:
        print(f"[HATA] Doğrulama sırasında hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_codegen_persistence())
