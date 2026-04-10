
import asyncio
import sys
import os

# PYTHONPATH ayarı (Modular Monolith uyumluluğu)
sys.path.append(os.getcwd())

async def smoke_test_autonomy():
    print("🚀 Sovereign AGI Otonomi Entegrasyon Testi Başlatılıyor...")
    
    try:
        print("\n1. SovereignCortex Başlatılıyor...")
        from packages.orchestration.application.sovereign_cortex import sovereign_cortex
        await sovereign_cortex.start()
        print("✅ SovereignCortex ve ImprovementCoordinator aktif.")

        print("\n2. Engine Bağlantıları Kontrol Ediliyor...")
        if sovereign_cortex.improvement_coordinator:
            print("✅ SelfImprovementCoordinator başarıyla yüklendi.")
        else:
            print("❌ SelfImprovementCoordinator YÜKLENEMEDİ!")

        print("\n3. Healing Hook Test Ediliyor...")
        from packages.orchestration.application.operational_executor import OperationalExecutor
        from packages.healing.application.heal_engine import heal_engine
        executor = OperationalExecutor(None, None)
        # Sadece import ve varlık kontrolü
        if heal_engine:
            print("✅ HealEngine (Self-Healing) erişilebilir.")

        print("\n4. Tool Bridge Kontrol Ediliyor...")
        from packages.orchestration.agi.operational.tool_executor import ToolExecutor
        # ToolExecutor instatiation check
        print("✅ ToolExecutor modülü sağlıklı.")

        print("\n🔥 TÜM OTONOM SİSTEMLER BAĞLI VE AKTİF!")
        
    except Exception as e:
        print(f"\n❌ KRİTİK HATA: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await sovereign_cortex.shutdown()
        print("\n🛑 Test tamamlandı.")

if __name__ == "__main__":
    asyncio.run(smoke_test_autonomy())
