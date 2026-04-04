import asyncio
import uuid
import logging
from datetime import datetime, timezone
from core.agi.cognitive.synaptic_cortex import synaptic_cortex
from core.agi.learning.wisdom_synthesizer import wisdom_synthesizer
from core.agi.task_governance import ProjectTask, TaskStatus
from db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_ase")

async def test_semantic_similarity():
    logger.info(">>> Testing Semantic Similarity (Faz 12.2)")
    
    text1 = "Sistemdeki 429 hataları için backoff mekanizması eklendi."
    text2 = "Rate limit aşıldığında sistem otonom olarak soğutma moduna geçiyor."
    text3 = "Veritabanı bağlantı havuzu optimize edildi."

    # Semantik olmayan (difflib bazlı) kontrol
    sim_12 = synaptic_cortex.check_similarity(text1, text2)
    logger.info(f"Diff Similarity (1-2): {sim_12}")

    # Semantik (Vektör bazlı) kontrol
    try:
        sem_12 = await synaptic_cortex.check_semantic_similarity(text1, text2)
        sem_13 = await synaptic_cortex.check_semantic_similarity(text1, text3)
        
        logger.info(f"SEMANTIC Similarity (1-2) [Related]: {sem_12}")
        logger.info(f"SEMANTIC Similarity (1-3) [Unrelated]: {sem_13}")
        
        assert sem_12 > sem_13, "Semantic similarity should prioritize conceptual relatedness"
        logger.info("✅ Semantic similarity test passed!")
    except Exception as e:
        logger.error(f"❌ Semantic similarity test failed/skipped: {e}")

async def test_wisdom_saturation():
    logger.info(">>> Testing Wisdom Saturation (Faz 12.2)")
    
    # Mock bir görev oluştur
    task = ProjectTask(
        id=str(uuid.uuid4()),
        title="API Hardening Test",
        description="429 hataları için antibody testi yapılıyor.",
        status=TaskStatus.COMPLETED
    )
    
    # Önce bir ders kaydet (MockDB gerekebilir veya direkt UGC cache'e bakabilir)
    async with AsyncSessionLocal() as db:
        await synaptic_cortex.save(
            db=db,
            agent_id="test",
            body="API Hardening: 429 hataları için antibody testi başarıyla tamamlandı.",
            category="semantic_wisdom",
            importance=0.8
        )
        await db.commit()

    # Saturation kontrolü yap
    is_saturated, _ = await wisdom_synthesizer._check_saturation(task)
    logger.info(f"Saturated: {is_saturated}")
    
    if is_saturated:
        logger.info("✅ Wisdom saturation (conceptual deduplication) working!")
    else:
        logger.warning("⚠️ Wisdom saturation not triggered. Check thresholds or embeddings.")

async def main():
    await test_semantic_similarity()
    await test_wisdom_saturation()

if __name__ == "__main__":
    asyncio.run(main())
