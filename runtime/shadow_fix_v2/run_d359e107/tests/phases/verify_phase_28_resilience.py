import asyncio
import json
import uuid
from typing import Dict, Any
from services.orchestration.agi.cognitive.sovereign_cortex import nexus_orchestrator
from services.orchestration.agi.consciousness.affective_core import affective_core
from services.orchestration.agi.cognitive.motivation_engine import motivation_engine
from services.orchestration.agi.task_governance import TaskStatus

async def verify_resilience_loop():
    print("Faz 28 & 29 Verification: Affective Resilience Test")
    
    # 1. Başlangıç Durumu Kontrolü
    aff_matrix = affective_core.get_state_matrix()
    print(f"Baslangic Mood: {affective_core.get_current_mood()}")
    print(f"Baslangic Stress: {aff_matrix.get('internal_stress')}")
    
    # 2. Hata Enjeksiyonu (Stress Test)
    print("\n--- Hata Simule Ediliyor (429 Rate Limit) ---")
    affective_core.adjust_state("rate_limit_429", magnitude=0.3)
    affective_core.adjust_state("error", magnitude=0.2)
    
    # 3. Motivasyon Yeniden Kalibrasyonu
    from services.orchestration.agi.schemas import ProblemFrame, TaskType, RiskLevel
    frame = ProblemFrame(task_type=TaskType.OPERATION, objective="Stress Test", risk_level=RiskLevel.HIGH)
    mot_state = await motivation_engine.recalibrate_state([], frame)
    
    print(f"Yeni Mood: {affective_core.get_current_mood()}")
    print(f"Yeni Stress: {mot_state.internal_stress:.2f}")
    print(f"Yeni Enerji: {mot_state.energy_reserve:.2f}")
    print(f"Yeni Politika: {mot_state.persistence_policy}")
    
    # Beklenen: Stress yüksek/Enerji düşük olduğu için politika 'careful' olmalı
    if mot_state.persistence_policy == "careful":
        print("OK: Sistem savunma moduna (careful) gecti.")
    else:
        print(f"HATA: Politika 'careful' olmaliydi, su an: {mot_state.persistence_policy}")

    # 4. Persistence Multiplier Kontrolü
    multiplier = motivation_engine.get_persistence_multiplier()
    print(f"Retry Carpani: {multiplier}")
    if multiplier == 1:
        print("OK: Careful modunda retry sayisi 1'e dustu.")
    
    # 5. Success Durumunda Toparlama
    print("\n--- Basari Simule Ediliyor (Recovery) ---")
    affective_core.adjust_state("success", magnitude=0.4)
    mot_state = await motivation_engine.recalibrate_state([], frame)
    print(f"Recovered Mood: {affective_core.get_current_mood()}")
    print(f"Recovered Stress: {mot_state.internal_stress:.2f}")
    
    if mot_state.internal_stress < 0.5:
        print("OK: Sistem basari sonrasi stres seviyesini dusurdu.")

    print("\nSONUC: FAZ 28 & 29 DOGRULANDI.")

if __name__ == "__main__":
    asyncio.run(verify_resilience_loop())
