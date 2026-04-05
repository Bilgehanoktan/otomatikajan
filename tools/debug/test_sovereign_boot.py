import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.agi.cognitive.sovereign_cortex import SovereignCortex

async def test_sovereign_init():
    print("--- Sovereign Cortex Başlatma Testi ---")
    cortex = SovereignCortex()
    
    # Start methodunu çağır (SelfUpdater burada yükleniyor)
    await cortex.start()
    
    if cortex.self_updater:
        print("[SUCCESS] SelfUpdater başarıyla yüklendi.")
    else:
        print("[FAILURE] SelfUpdater YÜKLENEMEDİ.")
        
    print(f"Birim Sayısı: {cortex.agent_count()}")
    print("--- Test Tamamlandı ---")

if __name__ == "__main__":
    asyncio.run(test_sovereign_init())
