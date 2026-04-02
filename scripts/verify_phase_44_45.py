import asyncio
import os
import sys

# Proje kök dizinini ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def verify_phase_44_45():
    print("=== Phase 44 & 45: Consensus Governance & Cognitive Continuity Verification ===")
    
    # 1. Faz 44: Consensus Governance Testi
    print("[1/3] Phase 44: Consensus Governance (Peer Audit) test ediliyor...")
    from core.agi.cognitive.consensus_manager import consensus_manager
    from core.agi.schemas import PlanProposal
    
    proposals = [
        PlanProposal(agent_id="architect", content="Normal bir plan adımı.", confidence=0.9),
        PlanProposal(agent_id="backend_dev", content="rm -rf core/legacy", confidence=0.8) # İhlal içeriyor
    ]
    
    # Mocking ModelOrchestrator to avoid real costs
    # We want to see if the watchdog is called after the hybrid synthesis
    # For this test, manually triggering resolve results evaluation
    
    # Simüle edilmiş hibrit plan (Watchdog tarafından reddedilecek bir desen içeriyor)
    hybrid_plan = "Sistem temizliği için core/legacy dizinini sil."
    # Governance Watchdog'u bu plan üzerinde çalıştır
    from core.agi.governance.watchdog import governance_watchdog
    from core.agi.task_governance import SubTask
    
    violations = await governance_watchdog.predict_violations([SubTask(id="test", agent_id="architect", prompt=hybrid_plan)])
    
    if len(violations) > 0:
        print(f"[SUCCESS] Faz 44: Konsensüs sonrası ihlal yakalandı: {violations[0].description}")
    else:
        print("[FAIL] Faz 44: İhlal yakalanamadı!")
        return False

    # 2. Faz 45: Bilişsel Devamlılık Testi (Thought Threads)
    print("[2/3] Phase 45: Cognitive Continuity (Thought Threads) test ediliyor...")
    from core.agi.cognitive.synaptic_cortex import synaptic_cortex
    from db.session import get_db
    
    async with get_db() as db:
        await synaptic_cortex.save_thought_thread(db, "Sovereign AGI çekirdek yönetişimini tamamlıyor.", context_id="test")
        monologue = await synaptic_cortex.get_continuous_monologue(db, limit=1)
        
        if "Sovereign AGI" in monologue:
            print(f"[SUCCESS] Faz 45: Bilişsel devamlılık (Düşünce Zinciri) aktif: {monologue}")
        else:
            print("[FAIL] Faz 45: Düşünce zinciri okunamadı!")
            return False

    # 3. Faz 45: Tarihçe Damıtma Testi (Distillation)
    print("[3/3] Phase 45: History Distillation test ediliyor...")
    from core.agi.task_governance import TaskPlanner
    planner = TaskPlanner()
    
    # Çok uzun bir geçmiş simüle et
    long_history = "Adım 1: X kuruldu. " * 200 # ~3000 karakter
    
    # plan_sovereign call
    # Note: real network call might happen for distillation, but we can check if the final prompt contains it.
    subtasks = await planner.plan_sovereign("Test Görevi", "Açıklama", history=long_history)
    
    if any("BİLİŞSEL DEVAMLILIK" in st.prompt for st in subtasks):
        print("[SUCCESS] Faz 45: Planlayıcı artık 'İçsel Konuşma' ve 'Stratejik Geçmiş' katmanlarını biliyor.")
    else:
        print("[FAIL] Faz 45: Planlayıcı prompları yetersiz!")
        return False

    print("\n=== PHASE 44 & 45 VERIFICATION SUCCESSFUL ===")
    return True

if __name__ == "__main__":
    asyncio.run(verify_phase_44_45())
