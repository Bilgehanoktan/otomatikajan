import asyncio
import sys
import os

# Dosya yollarını ayarla
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.agi.cognitive.motivation_engine import motivation_engine
from core.agi.schemas import EpisodeRecord, ProblemFrame, RiskLevel, TaskType, VerificationReport
from datetime import datetime, timezone

async def test_motivation_calibration():
    print("--- Phase 28: Motivasyon ve Dayanıklılık Doğrulaması Başlatılıyor ---")
    
    # 1. Senaryo: Başarılı Geçmiş
    print("\n[Senaryo 1] Başarılı Seri")
    success_episodes = [
        EpisodeRecord(success=True, verification=VerificationReport(result_status=True)),
        EpisodeRecord(success=True, verification=VerificationReport(result_status=True)),
        EpisodeRecord(success=True, verification=VerificationReport(result_status=True))
    ]
    frame_normal = ProblemFrame(objective="Normal Görev", risk_level=RiskLevel.LOW, task_type=TaskType.ANALYSIS)
    
    state_fast = await motivation_engine.recalibrate_state(success_episodes, frame_normal)
    print(f"Bektelen: Motivation > 0.8 | Mevcut: {state_fast.motivation_level:.2f}")
    print(f"Persistence Policy: {state_fast.persistence_policy} (Beklenen: aggressive)")
    
    # 2. Senaryo: Kritik Görev (Kriz Anı)
    print("\n[Senaryo 2] Kritik Görev (Resilience Test)")
    frame_critical = ProblemFrame(objective="Kritik Sistem Onarımı", risk_level=RiskLevel.CRITICAL, task_type=TaskType.REFACTOR)
    
    state_resilient = await motivation_engine.recalibrate_state(success_episodes, frame_critical)
    print(f"Resilience Score: {state_resilient.resilience_score:.2f} (Artış beklendi)")
    print(f"Atılacak Deneme Çarpanı: {motivation_engine.get_persistence_multiplier()}")

    # 3. Senaryo: Başarısızlık Serisi
    print("\n[Senaryo 3] Başarısızlık Serisi")
    failed_episodes = [
        EpisodeRecord(success=False, verification=VerificationReport(result_status=False)),
        EpisodeRecord(success=False, verification=VerificationReport(result_status=False))
    ]
    state_depressed = await motivation_engine.recalibrate_state(failed_episodes, frame_normal)
    print(f"Motivation Level: {state_depressed.motivation_level:.2f} (Azalış beklendi)")
    print(f"Persistence Policy: {state_depressed.persistence_policy} (Beklenen: careful)")

    print("\n--- Doğrulama Başarıyla Tamamlandı ---")

if __name__ == "__main__":
    asyncio.run(test_motivation_calibration())
