
import asyncio
import os
import json
from services.orchestration.agi.cognitive.goal_synthesizer import GoalSynthesizer
from services.orchestration.agi.cognitive.foresight_cortex import foresight_cortex
from services.orchestration.application.self_updater import SelfUpdater
from libs.llm.model_orchestrator import model_orchestrator

async def audit_goal_synthesis():
    print("\n[AUDIT] 1. Goal Synthesis Testi Başlatılıyor...")
    synth = GoalSynthesizer(model_orch=model_orchestrator)
    # Bu döngü negatif pattern'lerden yeni görevler üretir
    try:
        await synth.run_synthesis_cycle()
        print("[SUCCESS] Goal Synthesis döngüsü hatasız tamamlandı.")
    except Exception as e:
        print(f"[FAIL] Goal Synthesis hatası: {e}")

async def audit_foresight_simulation():
    print("\n[AUDIT] 2. Foresight Simulation Testi Başlatılıyor...")
    dummy_plan = {
        "title": "Database Migration to Vector Store",
        "summary": "Tüm ilişkisel logları yüksek performanslı bir vektör veritabanına taşıma planı.",
        "steps": ["Setup vector DB", "Map schemas", "Migrate data"]
    }
    try:
        timelines = await foresight_cortex.simulate_parallel_futures(dummy_plan)
        print(f"[SUCCESS] {len(timelines)} adet paralel gelecek senaryosu üretildi:")
        for t in timelines:
            print(f"  - {t.get('timeline_name')}: Risk={t.get('risk_score')} Utility={t.get('utility_score')}")
    except Exception as e:
        print(f"[FAIL] Foresight hatası: {e}")

async def audit_self_updater():
    print("\n[AUDIT] 3. Self-Updater & ShadowRunner Testi Başlatılıyor...")
    # Zararsız bir deneme yapalım: libs/utils/string_utils.py (varsa) veya benzeri bir yere yeni bir metod ekleme önerisi
    # Önce dosyanın varlığını kontrol edelim
    target_file = "libs/utils/health_check.py" # Örnek bir dosya
    if not os.path.exists(target_file):
        # Dosya yoksa oluştur
        os.makedirs("libs/utils", exist_ok=True)
        with open(target_file, "w") as f:
            f.write("def check(): return True\n")
    
    updater = SelfUpdater(model_orch=model_orchestrator)
    instruction = "Lütfen bu dosyaya sistemin çalışma süresini (uptime) saniye cinsinden döndüren bir 'get_uptime' fonksiyonu ekle."
    
    try:
        # modify_system_file yerine propose_fix kullanarak sadece öneriyi görelim (canlı kod bozulmasın)
        proposed_code = await updater.propose_fix(target_file, instruction)
        print("[SUCCESS] Yeni kod önerisi üretildi:")
        print("--- PROPOSED CODE ---")
        print(proposed_code)
        print("----------------------")
        
        # Şimdi ShadowRunner ile validate edelim (bu manuel bir test)
        from services.orchestration.application.shadow_runner import ShadowRunner
        runner = ShadowRunner()
        print("[INFO] ShadowRunner validasyonu başlatılıyor...")
        val = runner.validate_candidate(target_file, proposed_code)
        print(f"[RESULT] Syntax OK: {val.get('syntax_ok')}")
        print(f"[RESULT] Pytest OK: {val.get('pytest_ok')} (Skipped: {val.get('pytest_skipped')})")
        
        # Temizlik
        import shutil
        if val.get("shadow_root"):
            shutil.rmtree(val.get("shadow_root"), ignore_errors=True)
            
    except Exception as e:
        print(f"[FAIL] Self-Updater hatası: {e}")

async def main():
    print("=== SOVEREIGN AGI SYSTEM DEEP AUDIT ===")
    await audit_goal_synthesis()
    await audit_foresight_simulation()
    await audit_self_updater()
    print("\n=== AUDIT TAMAMLANDI ===")

if __name__ == "__main__":
    asyncio.run(main())
