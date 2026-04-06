import asyncio
import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import select, delete
from packages.persistence.session import AsyncSessionLocal, _get_engine as get_engine
from packages.persistence.models import LLMCostLog, SovereignModelPolicy, Base, Project, SubTask
from packages.orchestration.agi.operational.nas_optimizer import nas_optimizer
from packages.llm_gateway.model_orchestrator import ModelOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyPhase64")

async def setup_mock_data():
    """Mock performans verileri oluştur (Gemini kazanmalı)."""
    async with AsyncSessionLocal() as db:
        # Eski verileri temizle (opsiyonel)
        await packages.persistence.execute(delete(LLMCostLog))
        await packages.persistence.execute(delete(SovereignModelPolicy))
        
        # 1. Gemini: Hızlı, Ucuz, Başarılı (Architect rolü için)
        for _ in range(10):
            packages.persistence.add(LLMCostLog(
                provider="gemini",
                model="gemini-1.5-flash",
                agent_role="architect",
                success=True,
                latency_s=0.5,
                cost_usd=0.00001,
                input_tokens=100,
                output_tokens=100
            ))
            
        # 2. OpenAI: Yavaş, Pahalı (Architect rolü için)
        for _ in range(5):
            packages.persistence.add(LLMCostLog(
                provider="openai",
                model="gpt-4o",
                agent_role="architect",
                success=True,
                latency_s=2.5,
                cost_usd=0.0005,
                input_tokens=100,
                output_tokens=100
            ))
            
        await packages.persistence.commit()
    logger.info("Mock veriler yüklendi: Gemini (Hızlı/Ucuz) vs OpenAI (Yavaş/Pahalı)")

async def verify_nas():
    orch = ModelOrchestrator()
    
    # 1. Başlangıçta statik politika mı var?
    static_chain = await orch.get_fallback_chain("architect")
    logger.info(f"Başlangıç Zinciri: {static_chain}")

    # 2. NAS Optimizasyonu çalıştır
    logger.info("NAS Optimizasyonu başlatılıyor...")
    await nas_optimizer.optimize_all_roles()
    
    # 3. DB'de politikanın oluştuğunu kontrol et
    async with AsyncSessionLocal() as db:
        res = await packages.persistence.execute(select(SovereignModelPolicy).where(SovereignModelPolicy.agent_role == "architect"))
        policy = res.scalar_one_or_none()
        
        if not policy:
            logger.error("HATA: NAS politikası veritabanına yazılmadı!")
            return False
            
        logger.info(f"YENİ POLİTİKA: {policy.agent_role} -> Kazanan: {policy.winner_provider}")
        
        if policy.winner_provider != "gemini":
            logger.error(f"HATA: Beklenen kazanan 'gemini', bulunan '{policy.winner_provider}'")
            return False

    # 4. Orchestrator'ın yeni politikayı kullandığını doğrula
    new_chain = await orch.get_fallback_chain("architect")
    logger.info(f"Dinamik Zincir: {new_chain}")
    
    if new_chain[0] != "gemini":
        logger.error("HATA: ModelOrchestrator yeni politikayı uygulamadı!")
        return False

    logger.info("PHASE 64 DOĞRULAMASI BAŞARILI: NAS dinamik yönlendirmesi aktif!")
    return True

if __name__ == "__main__":
    async def main():
        # Veritabanı tablolarının olduğundan emin ol
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        await setup_mock_data()
        success = await verify_nas()
        if not success:
            exit(1)
            
    asyncio.run(main())
