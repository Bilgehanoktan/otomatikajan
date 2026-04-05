import asyncio
import uuid
import sys
import os

# Root ekle
sys.path.append(os.getcwd())

from core.agi.central_executive import central_executive
from core.agi.schemas import SourceType, UnifiedInput
from db.session import session_scope
from core.agi.cognitive.synaptic_cortex import synaptic_cortex

async def test_agi_cognitive_loop_v25():
    print("--- AGI Faz 21-25 Bilişsel Döngü Doğrulaması Başlatılıyor ---")
    
    # SRE: SQLite Tablo Garantisi (Sync metadata races are real)
    import aiosqlite
    async with aiosqlite.connect("./cortex_local.db") as db_raw:
        await db_raw.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id CHAR(32) PRIMARY KEY,
                agent_id VARCHAR(64) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(64) NOT NULL,
                importance FLOAT NOT NULL,
                metadata_ TEXT,
                tags TEXT,
                expires_at DATETIME,
                project_id VARCHAR(64),
                created_at DATETIME NOT NULL
            )
        """)
        await db_raw.commit()
    print("[SRE] SQLite 'memories' tablosu doğrulandı.")

    from db.session import init_db
    await init_db()
    
    input_id = uuid.uuid4()
    raw_input = "Sistemin bellek yönetimini optimize et ve bir refaktör öner."
    
    # Adım 1: Yürütme Döngüsü
    print(f"\n[DÖNGÜ] Girdi İşleniyor: {raw_input}")
    episode = await central_executive.execute_thought_cycle(
        raw_input=raw_input,
        source=SourceType.USER_MESSAGE,
        input_id=str(input_id)
    )
    
    print(f"\n[SONUÇ] Başarı: {episode.success}")
    print(f"[SONUÇ] Karar Hedefi: {episode.problem_frame.objective}")
    print(f"[SONUÇ] Metacognitive Skor: {episode.metacognitive_score}")
    
    # Adım 2: Hafıza Kaydı Kontrolü
    async with session_scope() as db:
        memories = await synaptic_cortex.search(db, query="", project_id=str(input_id))
        print(f"\n[HAFIZA] Proje ID '{input_id}' için bulunan kayıt sayısı: {len(memories)}")
        for m in memories:
            print(f" - [{m['category']}] {m['body'][:100]}...")

    # Adım 3: Theory of Mind Kontrolü
    from core.agi.cognitive.theory_of_mind import theory_of_mind
    inferred = theory_of_mind.get_inferred_state()
    print(f"\n[TOM] Tahmin Edilen Kullanıcı Modeli: {inferred}")
    
    print("\n--- Doğrulama Tamamlandı ---")

if __name__ == "__main__":
    asyncio.run(test_agi_cognitive_loop_v25())
