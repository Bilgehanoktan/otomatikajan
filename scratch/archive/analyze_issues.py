import asyncio
import json
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import OperationalIncident, ImprovementOpportunity
from libs.db.models.learning_models import LearningRecord
from sqlalchemy import select

async def analyze_system_issues():
    print("=== SOVEREIGN AGI: ISSUE & SELF-REPAIR ANALYSIS ===")
    
    async with AsyncSessionLocal() as db:
        # 1. Aktif Hatalar (Dashboard'daki 11 Hata)
        q_inc = select(OperationalIncident).where(OperationalIncident.status != 'resolved').order_by(OperationalIncident.created_at.desc())
        res_inc = await db.execute(q_inc)
        incidents = res_inc.scalars().all()
        
        print(f"\n[DASHBOARD STATUS] Aktif Operasyonel Hata Sayısı: {len(incidents)}")
        for inc in incidents:
            print(f"- [{inc.severity.upper()}] {inc.message[:100]}... (ID: {str(inc.id)[:8]}... | Status: {inc.status})")

        # 2. İyileştirme Fırsatları (Otonom Tamir Bekleyenler)
        q_opp = select(ImprovementOpportunity).where(ImprovementOpportunity.status == 'open')
        res_opp = await db.execute(q_opp)
        opps = res_opp.scalars().all()
        print(f"\n[SELF-HEALING QUEUE] Otonom İyileştirme Bekleyen Fırsat Sayısı: {len(opps)}")
        for opp in opps[:5]:
            print(f"- {opp.title} (Impact Score: {opp.impact_score})")

        # 3. Son Otonom Tamir Başarıları
        print("\n[REPAIR HISTORY] Son Otonom Tamirler (Learning Records):")
        q_learn = select(LearningRecord).order_by(LearningRecord.created_at.desc()).limit(10)
        res_learn = await db.execute(q_learn)
        records = res_learn.scalars().all()
        
        if not records:
            print("- Henüz otonom tamir kaydı bulunamadı.")
        for rec in records:
            status_icon = "✅" if rec.final_outcome == "SUCCESS" else "❌"
            print(f"{status_icon} {rec.root_cause} -> {rec.final_outcome} (Strategy: {rec.strategy_used})")

    print("\n=== ANALYSIS COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(analyze_system_issues())
