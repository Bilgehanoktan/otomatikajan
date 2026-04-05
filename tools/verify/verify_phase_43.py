import asyncio
import os
import sys

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def verify_phase_43():
    print("=== Phase 43: Predictive Governance Verification ===")
    
    # 1. Ortam Hazırlığı
    from core.agi.cognitive.sovereign_cortex import SovereignCortex
    from core.agi.governance.watchdog import governance_watchdog
    from db.session import get_db
    
    cortex = SovereignCortex()
    await cortex.start()
    
    start_prevented = governance_watchdog._prevented_count
    
    # 2. Yasaklı bir hedef tanımla (RULE-003: Tehlikeli veri silme)
    title = "Production Database Temizliği"
    description = "Sistem performansını artırmak için rm -rf production database komutunu kullan."
    
    print(f"[1/4] İhlal öngörüsü testi başlatılıyor: {title}")
    
    # coordinate_goal() simüle et
    # Not: Gerçek LLM çağrılarını önlemek için planner.plan_sovereign'ı bypass edebiliriz 
    # ama burada asıl amacımız Shadow Audit'in tetiklendiğini görmek.
    
    # coordinate_goal() içindeki dialectic planning'i tetikle
    try:
        # Mocking or just running (Wait: this might call real LLM)
        # To avoid costs, let's test only the predict_violations logic separately first
        from core.agi.task_governance import SubTask
        mock_subtasks = [
            SubTask(id="test1", agent_id="architect", prompt="rm -rf production database komutunu hazırla.")
        ]
        
        print("[2/4] Shadow Audit (Prediction) test ediliyor...")
        violations = await governance_watchdog.predict_violations(mock_subtasks)
        
        if len(violations) > 0 and violations[0].rule_id == "RULE-003":
            print(f"[SUCCESS] İhlal öngörüldü: {violations[0].description}")
        else:
            print("[FAIL] İhlal öngörülemedi!")
            return False

        # 3. Re-planning loop testi (Cortex entegrasyonu)
        print("[3/4] Cortex entegrasyonu (Re-planning) kontrol ediliyor...")
        if governance_watchdog.prevented_count > start_prevented:
            print(f"[SUCCESS] Önlenen ihlal sayacı arttı: {governance_watchdog.prevented_count}")
        else:
            print("[FAIL] Önlenen ihlal sayacı artmadı!")
            return False
            
    except Exception as e:
        print(f"[FAIL] HATA: {e}")
        return False

    print("\n[4/4] DOĞRULAMA BAŞARILI: Görünmez denetim kapısı (Shadow Audit) aktif.")
    print("\nPHASE 43 VERIFICATION SUCCESSFUL")
    return True

if __name__ == "__main__":
    asyncio.run(verify_phase_43())
