import asyncio
import sys
import os
from types import SimpleNamespace

# Dosya yollarını ayarla
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from packages.orchestration.agi.cognitive.motivation_engine import motivation_engine
from packages.orchestration.agi.schemas import ProblemFrame, RiskLevel, TaskType
from datetime import datetime, timezone

async def test_motivation_calibration():
    print("--- Phase 28: Motivasyon ve Dayanıklılık Doğrulaması Başlatılıyor ---")
    
    # 1. Senaryo: Başarılı Geçmiş
    print("\n[Senaryo 1] Başarılı Seri")
    # MotivationEngine getattr(e, "success") kullanıyor, bu yüzden SimpleNamespace yeterli
    success_episodes = [
        SimpleNamespace(success=True, importance=0.8),
        SimpleNamespace(success=True, importance=0.9),
        SimpleNamespace(success=True, importance=0.7)
    ]
    frame_normal = ProblemFrame(objective="Normal Görev", risk_level=RiskLevel.LOW, task_type=TaskType.ANALYSIS)
    
    state_fast = await motivation_engine.recalibrate_state(success_episodes, frame_normal)
    print(f"Mevcut: {state_fast.motivation_level:.2f}")
    print(f"Persistence Policy: {state_fast.persistence_policy} (Beklenen: aggressive)")
    
    # 2. Senaryo: Kritik Görev (Kriz Anı)
    print("\n[Senaryo 2] Kritik Görev (Resilience Test)")
    frame_critical = ProblemFrame(objective="Kritik Sistem Onarımı", risk_level=RiskLevel.CRITICAL, task_type=TaskType.FIX)
    
    state_resilient = await motivation_engine.recalibrate_state(success_episodes, frame_critical)
    print(f"Resilience Score: {state_resilient.resilience_score:.2f} (Artış beklendi)")
    print(f"Atılacak Deneme Çarpanı: {motivation_engine.get_persistence_multiplier()}")
 
    # 3. Senaryo: Başarısızlık Serisi
    print("\n[Senaryo 3] Başarısızlık Serisi")
    failed_episodes = [
        SimpleNamespace(success=False, importance=0.8),
        SimpleNamespace(success=False, importance=0.5)
    ]
    state_depressed = await motivation_engine.recalibrate_state(failed_episodes, frame_normal)
    print(f"Motivation Level: {state_depressed.motivation_level:.2f} (Azalış beklendi)")
    print(f"Persistence Policy: {state_depressed.persistence_policy} (Beklenen: careful)")

    print("\n--- Doğrulama Başarıyla Tamamlandı ---")

if __name__ == "__main__":
    asyncio.run(test_motivation_calibration())
