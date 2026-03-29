import asyncio
import sys
import os
import json
from datetime import datetime, timezone

# 1. Project Root'u bul ve sys.path'e ekle
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.orchestrator import orchestrator
from core.job_queue import job_queue
from db.session import AsyncSessionLocal
from db.models import ProjectStatus

async def simulate_agent_task():
    print("--- AJAN GÖREV SİMÜLASYONU BAŞLATILIYOR ---")
    print(f"Zaman: {datetime.now(timezone.utc).isoformat()}")
    print("-" * 50)

    # 1. Orkestratörü Başlat (Ajanları yükle)
    await orchestrator.start()
    print(f"[OK] Orkestratör hazır. Kayıtlı ajan sayısı: {orchestrator.agent_count()}")

    # 2. Test Görevi Tanımla
    title = "Sistem Sağlık ve Beceri Entegrasyon Testi"
    description = """
    Bu bir otonom test görevidir. 
    Lütfen sistemdeki 'debugging' ve 'optimization' becerilerinin (skills) 
    mevcut iş akışına doğru entegre edilip edilmediğini kontrol et.
    Async/Await yapısında bir hata (traceback) var mı incele.
    """

    print(f"[*] Görev oluşturuluyor: {title}")
    
    # 3. Manuel Çalıştırma (API/Docker bağımsız)
    try:
        # Ajanların akışını (DAG) simüle et
        # Bu işlem gerçek ajan mantığını tetikleyecektir
        result_task = await orchestrator.run_project(
            title=title,
            description=description,
            workflow_template="standard",
            quality_profile="high"
        )

        print("-" * 50)
        print(f"[SONUÇ] Görev Durumu: {result_task.status}")
        print(f"[SONUÇ] Görev ID: {result_task.id}")
        
        # Subtask çıktılarını kontrol et
        for st in result_task.subtasks:
            print(f"  > Agent [{st.agent_id}]: {st.status}")
            if st.quality_score:
                print(f"    Kalite Skoru: {st.quality_score:.2f}")

        if result_task.status != "failed":
            print("-" * 50)
            print("[TEBRİKLER] Ajanlar başarıyla çalıştı ve rapor üretti!")
            return True
        else:
            print("[HATA] Ajan akışında bir sorun oluştu.")
            return False

    except Exception as e:
        print(f"[KRİTİK HATA] Test sırasında istisna oluştu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    success = asyncio.run(simulate_agent_task())
    sys.exit(0 if success else 1)
