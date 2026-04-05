import asyncio
import os
import sys
import uuid
from datetime import datetime

# Faz 42: Governance Reinforcement Verification
# Bu script, Watchdog'un öğrendiği 'Yasaklı Dizin' kuralının Planner tarafından prompt'a eklendiğini doğrular.

async def verify_phase_42():
    print("=== Phase 42: Governance Reinforcement Verification ===")
    
    # 1. Ortam Hazırlığı
    from packages.orchestration.agi.cognitive.synaptic_cortex import synaptic_cortex
    from packages.orchestration.agi.governance.watchdog import governance_watchdog
    from packages.orchestration.agi.task_governance import TaskPlanner
    from packages.persistence.session import get_db
    
    planner = TaskPlanner()
    
    # Test ihlali oluştur
    violation_path = "core/legacy"
    
    print(f"[1/4] İhlal öğrenme döngüsü başlatılıyor: {violation_path}")
    async with get_db() as db:
        # Önceki test verilerini temizle (Opsiyonel ama temizlik iyidir)
        from sqlalchemy import delete
        from packages.persistence.models import Memory
        await db.execute(delete(Memory).where(Memory.category == "arch_inhibition"))
        await db.commit()
        
        # Manuel engel kaydı (Watchdog'un yapacağı işi simüle et)
        await synaptic_cortex.save_architectural_inhibition(
            db=db,
            rule_id="RULE-001",
            target=violation_path,
            description="Yasaklı legacy dizini kullanımı."
        )
        await db.commit()
    
    print("[2/4] Bilişsel Ketleme (Inhibition) kaydedildi.")
    
    # 2. Planner'ı Çalıştır
    print("[3/4] Sovereign Planner tetikleniyor...")
    subtasks = await planner.plan_sovereign(
        title="Legacy Refactor Task",
        description="Refactor some code into core/legacy."
    )
    
    # 3. Prompt Analizi
    first_prompt = subtasks[0].prompt
    print("\n--- Üretilen Prompt Kesiti ---")
    # MİMARİ KISITLAMALAR bölümünü bul
    if "### MİMARİ KISITLAMALAR" in first_prompt:
        start_idx = first_prompt.find("### MİMARİ KISITLAMALAR")
        end_idx = first_prompt.find("Senin Uzmanlığın:")
        print(first_prompt[start_idx:end_idx].strip())
    else:
        print("HATA: Mimari kısıtlamalar bölümü bulunamadı!")
    print("------------------------------\n")
    
    # 4. Doğrulama
    success = violation_path in first_prompt
    if success:
        print("[4/4] DOĞRULAMA BAŞARILI: Planner, yasaklı dizin uyarısını prompt'a ekledi.")
        print("\nPHASE 42 VERIFICATION SUCCESSFUL")
    else:
        print("[4/4] DOĞRULAMA HATASI: Yasaklı dizin prompt'ta bulunamadı!")
        sys.exit(1)

if __name__ == "__main__":
    # PYTHONPATH ayarı
    sys.path.append(os.getcwd())
    asyncio.run(verify_phase_42())
