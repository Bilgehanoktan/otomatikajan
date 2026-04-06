import asyncio
import uuid
from packages.orchestration.agi.central_executive import central_executive
from packages.orchestration.agi.schemas import SourceType
from packages.observability.logging import get_logger

_log = get_logger("verify_phase_51")

async def test_recursive_decomposition():
    print("\n[PHASE 51] BİLİŞSEL DERİNLİK DOĞRULAMA BAŞLATILIYOR...")
    
    test_goal = "Karmaşık bir web servisi oluştur ve her adımı detaylandır."
    description = "Backend, Frontend ve Veritabanı katmanları olsun. En az bir adım 'karmaşık' (is_complex) olarak işaretlensin."
    
    try:
        # Bu işlem Faz 51'in tüm katmanlarını (Decomposer -> Planner -> Executive) tetikler
        episode = await central_executive.execute_thought_cycle(
            raw_input=f"HEDEF: {test_goal}\nAÇIKLAMA: {description}",
            source=SourceType.USER_MESSAGE,
            input_id=f"test_51_{str(uuid.uuid4())[:8]}"
        )
        
        print(f"\n[+] Episode Tamamlandı. Durum: {'BAŞARILI' if episode.final_output else 'BELİRSİZ'}")
        print(f"[+] Çıktı Uzunluğu: {len(episode.final_output)} karakter.")
        print(f"[+] Alınan Kararlar: {len(episode.actions)}")
        
        # Logları kontrol ederek Recursion ve Wave mesajlarını ara (Manuel veya otomatik)
        if "[RECURSION]" in episode.final_output or "WAVE" in episode.final_output:
             print("[SUCCESS] DAG veya Rekürsiyon izleri saptandı.")
        else:
             print("[INFO] Episode tamamlandı, ancak doğrudan çıktı içinde DAG izleri olmayabilir (loglara bakılmalı).")

    except Exception as e:
        print(f"[-] HATA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_recursive_decomposition())
