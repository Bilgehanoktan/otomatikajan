import asyncio
import uuid
import sys
import os
from datetime import datetime, timezone

# Add current directory to path
sys.path.append(os.getcwd())

from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from db.session import AsyncSessionLocal
from db.models import Project, SubTask, TaskPriority, Memory

async def run_integration_test():
    print("--- [FAZ 70-72] ENTEGRASYON TESTİ V2: DERİN BELLEK VE HATA ÖĞRENİMİ ---")
    
    async with AsyncSessionLocal() as db:
        # 1. KASITLI BİR HATA/DERS KAYDINI HAFIZAYA İŞLE (Negative Lesson)
        error_msg = "Database portu (5433) yanlış konfigüre edildiği için sistem çöktü."
        print(f"1. Geçmiş hata kaydı oluşturuluyor: {error_msg}")
        
        # UGC'ye negatif ders kaydet (Memory tablosuna)
        # Memory tablosunda body kolonunun ismi 'content' idi (synaptic_cortex.py'ye göre)
        await synaptic_cortex.save_negative_lesson(
            db=db,
            agent_id="db_specialist",
            body=error_msg,
            importance=0.9,
            metadata={"source": "v12.1-legacy-crash"}
        )
        await db.commit()
        print("   [BAŞARILI] Geçmiş ders hafızaya işlendi.")

        # 2. AYNI KONUYLA İLGİLİ YENİ BİR GÖREV SİMÜLASYONU
        # SubTask context'i başlangıçta boş ancak Nexus'ta doldurulacak
        subtask_title = "Database Configuration"
        subtask_prompt = "modify database ports to 5433"
        
        print(f"2. Yeni görev simüle ediliyor: {subtask_title}")

        # 3. SOVEREIGN CORTEX NEXUS LOGIĞINI ÇALIŞTIR VE RECALL'I GÖZLEMLE
        print("3. Sovereign Cortex Nexus tetikleniyor (Long-Horizon Recall)...")
        
        # Nexus'un içindeki memory recall kısmını simüle ediyoruz:
        print("   [MEMORY] Ajan için derin bellek taraması başlatılıyor...")
        # SynapticCortex.search_with_causal_anchoring çağrıyoruz
        past_lessons = await synaptic_cortex.search_with_causal_anchoring(
            db=db,
            query=f"{subtask_title} {subtask_prompt}",
            top_k=3
        )
        
        if past_lessons:
            print(f"   [MEMORY] {len(past_lessons)} adet geçmiş deneyim BULUNDU.")
            historical_provisos = []
            for m in past_lessons:
                body = m.get('body') or m.get('content') # Support both naming conventions
                cat = m.get('category', 'lesson')
                historical_provisos.append(f"[{cat}] {body}")
            
            print(f"   [FINAL-WISDOM] Enjekte edilecek veri: {historical_provisos}")
            
            # Doğrulama: Kaydettiğimiz hata mesajı burada mı?
            match_found = any(error_msg in p for p in historical_provisos)
            if match_found:
                print(f"\n[TEST BAŞARILI] Sistem geçmiş hatayı hatırladı (Recall Success).")
                print(f"AGI YETENEĞİ: 'FAILURE LEARNING' KANITLANDI.")
            else:
                print(f"\n[TEST BAŞARISIZ] Geçmiş ders hatırlanamadı. Sonuçlar: {historical_provisos}")
        else:
            print(f"\n[TEST BAŞARISIZ] Bellek taraması sonuç dönmedi.")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
