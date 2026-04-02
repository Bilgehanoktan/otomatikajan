"""
AGI Sovereign Patching Doğrulama Testi (Phase 45.0).
Sistemin kendi kodunu otonom olarak (Sovereign Evolution) yamama ve 
Provenance Engine üzerinden izlenebilirlik oluşturma kapasitesini test eder.
"""
import asyncio
import os
import shutil
from sqlalchemy import select
from db.session import AsyncSessionLocal, init_db
from db.models import Memory
from core.agi.adaptation.sovereign_evolution_45 import sovereign_evolution_45
from core.agi.operational.patching_sandbox import patching_sandbox
from observability.logging import get_logger

_log = get_logger("agi_self_patch_verify")

# Test Dosyası
TEST_FILE = "e:/ai_company_faz12.1/scripts/test_patch_target.py"

async def setup_test_environment():
    """Test için dummy dosya ve başlangıç durumunu hazırlar."""
    content = 'def hello():\n    print("LOG: OLD_VERSION_TEST")\n'
    with open(TEST_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    _log.info(f"Test dosyası oluşturuldu: {TEST_FILE}")

async def inject_policy_proposal(db):
    """Veritabanına otonom bir iyileştirme önerisi (Policy) ekler."""
    policy_data = {
        "title": "Update Logging in test_patch_target",
        "proposed_rule": f"Change print in '{TEST_FILE}' to use '[VERIFIED] NEW_VERSION_TEST'",
        "reason": "Test of Phase 36-40 Self-Patching Engine",
        "status": "pending"
    }
    
    # Eskileri temizle (opsiyonel)
    # stmt = select(Memory).where(Memory.category == "policy_proposal")
    # result = await db.execute(stmt)
    
    new_mem = Memory(
        agent_id="test_evolution",
        category="policy_proposal",
        body="Self-Patching Test Policy",
        metadata_=policy_data,
        importance=0.9
    )
    db.add(new_mem)
    await db.commit()
    _log.info("Test politikası veritabanına enjekte edildi.")

async def verify_patch_result():
    """Dosyanın güncellenip güncellenmediğini kontrol eder."""
    if not os.path.exists(TEST_FILE):
        return False, "Test dosyası kayboldu!"
        
    with open(TEST_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "NEW_VERSION_TEST" in content and "OLD_VERSION_TEST" not in content:
        return True, "Yama BAŞARIYLA uygulandı ve doğrulandı!"
    else:
        return False, f"Yama uygulanamadı. İçerik: {content}"

async def main():
    _log.info("--- AGI SELF-PATCHING DOĞRULAMA TESTİ BAŞLATILIYOR ---")
    
    # 1. Hazırlık
    await init_db()
    await setup_test_environment()
    
    async with AsyncSessionLocal() as db:
        # 2. Politika enjeksiyonu
        await inject_policy_proposal(db)
        
        # 3. Evolution Döngüsünü çalıştır
        _log.info("Sovereign Evolution Engine manuel tetikleniyor...")
        await sovereign_evolution_45.evolve_system(db)
        
    # 4. Doğrulama
    success, msg = await verify_patch_result()
    if success:
        _log.info(f"[PASSED] {msg}")
        # Cleanup
        if os.path.exists(TEST_FILE):
             os.remove(TEST_FILE)
    else:
        _log.error(f"[FAILED] {msg}")

if __name__ == "__main__":
    asyncio.run(main())
