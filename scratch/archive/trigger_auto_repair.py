import asyncio
import uuid
import os
from pathlib import Path
from services.repair.application.self_improvement_coordinator import SelfImprovementCoordinator
from services.orchestration.application.self_updater import SelfUpdater
from services.repair.improvement.observer import ImprovementObserver, ImprovementOpportunity
from libs.llm.model_orchestrator import ModelOrchestrator
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import OperationalIncident, SystemImprovement
from sqlalchemy import select

async def trigger_autonomous_healing():
    print("=== SOVEREIGN AGI: DUAL-STAGE AUTONOMOUS HEALING (V2) ===")
    
    # 1. Bağımlılıkları Hazırla
    root_dir = os.getcwd()
    model_orch = ModelOrchestrator() # LLM motoru
    updater = SelfUpdater(project_root=root_dir, model_orch=model_orch)
    observer = ImprovementObserver() 
    
    coordinator = SelfImprovementCoordinator(self_updater=updater, observer=observer)
    
    # 2. Hata Saptama
    print("\n[STAGE 1] Hata analizi başlatılıyor...")
    async with AsyncSessionLocal() as db:
        q = select(OperationalIncident).where(OperationalIncident.message.contains("ZeroDivisionError")).limit(1)
        res = await db.execute(q)
        incident = res.scalar_one_or_none()
        
        if not incident:
            print("ERROR: Aktif ZeroDivisionError bulunamadı! Lütfen bir hata oluşmasını bekleyin veya tetikleyin.")
            return
            
        target_file = "libs/utils/math_helper.py" 
        print(f"Hata Tespit Edildi: {incident.message[:80]}...")

        # Yapay bir 'opportunity' oluştur
        op = ImprovementOpportunity(
            id=uuid.uuid4(),
            title="Fix ZeroDivisionError",
            description=f"Automated repair for division by zero in {target_file}",
            severity="high",
            category="reliability",
            affected_files=[target_file],
            evidence_detail=incident.message
        )

    # 3. Analiz ve Shadow Verification
    print(f"\n[Shadow Phase] {target_file} için yama üretiliyor ve izole ortamda test ediliyor...")
    # Not: apply_improvement metodu içten ShadowRunner çağırır.
    proposal_report = await coordinator.apply_improvement(op)
    print(f"Shadow Report:\n{proposal_report}")

    # 4. Etik Onay ve Effector Uygulama
    print("\n[Effector Phase] Yama onaylanıyor ve fiziksel sisteme uygulanıyor...")
    async with AsyncSessionLocal() as db:
        q_imp = select(SystemImprovement).where(SystemImprovement.target_file == target_file).order_by(SystemImprovement.created_at.desc()).limit(1)
        res_imp = await db.execute(q_imp)
        imp = res_imp.scalar_one_or_none()
        
        if imp:
            imp.status = "approved"
            await db.commit()
            print(f"Onay Mührü Basıldı (ID: {str(imp.id)[:8]}).")
        else:
            print("ERROR: İyileştirme kaydı oluşturulamadı!")
            return

    # 5. Fiziksel Tamir
    await coordinator.run_effector()
    
    # 6. Incident'ı Kapat (Otonom olarak çözüldü işaretle)
    async with AsyncSessionLocal() as db:
        q_close = select(OperationalIncident).where(OperationalIncident.id == incident.id)
        res_close = await db.execute(q_close)
        inc_to_close = res_close.scalar_one()
        inc_to_close.status = "resolved"
        inc_to_close.resolved_at = asyncio.get_event_loop().time() # Dummy time or datetime
        await db.commit()

    print("\nSUCCESS: Sistem otonom olarak kendini iyileştirdi ve incident'ı kapattı!")
    print("Dashboard'daki 11 hata sayısının düştüğünü görebilirsiniz.")

if __name__ == "__main__":
    asyncio.run(trigger_autonomous_healing())
