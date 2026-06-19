
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from libs.db.session import AsyncSessionLocal
from libs.db.models.governance_models import GovernorCalibrationRecord, CalibrationStatus

async def seed_calibrations():
    print("[*] Kalibrasyon verileri tohumlaniyor...")
    
    async with AsyncSessionLocal() as db:
        # Mevcut verileri temizle (opsiyonel, ama temiz bir sayfa iyidir)
        # result = await db.execute(select(GovernorCalibrationRecord))
        # for row in result.scalars():
        #     await db.delete(row)
        
        calibrations = [
            {
                "parameter_name": "AUTO_APPROVE_CONFIDENCE_THRESHOLD",
                "old_value": 0.850,
                "proposed_value": 0.920,
                "change_reason": "Son 14 gündeki False Positive oranındaki %4'lük artış nedeniyle güven eşiği yükseltildi.",
                "confidence_score": 0.89,
                "window_days": 14,
                "sample_size": 1240,
                "status": CalibrationStatus.PROPOSED
            },
            {
                "parameter_name": "RISK_WEIGHT_LATENCY_IMPACT",
                "old_value": 0.150,
                "proposed_value": 0.250,
                "change_reason": "Gecikme süresinin kullanıcı memnuniyeti üzerindeki korelasyonu arttı. Gecikme ağırlığı normalize edildi.",
                "confidence_score": 0.72,
                "window_days": 30,
                "sample_size": 4500,
                "status": CalibrationStatus.PROPOSED
            },
            {
                "parameter_name": "MAX_CONCURRENT_AGENT_TASK_LIMIT",
                "old_value": 50.0,
                "proposed_value": 75.0,
                "change_reason": "Cluster kaynak kullanım verimliliği arttığı için eş zamanlı görev limiti genişletildi.",
                "confidence_score": 0.95,
                "window_days": 7,
                "sample_size": 850,
                "status": CalibrationStatus.APPLIED,
                "applied_value": 75.0,
                "applied_at": datetime.now(timezone.utc) - timedelta(days=1),
                "approved_by": "SYSTEM_AUTO"
            },
            {
                "parameter_name": "QUORUM_APPROVAL_TIMEOUT_SEC",
                "old_value": 3600.0,
                "proposed_value": 1800.0,
                "change_reason": "Eskalasyonların çözüm süresini hızlandırmak için timeout süresi düşürüldü.",
                "confidence_score": 0.65,
                "window_days": 14,
                "sample_size": 120,
                "status": CalibrationStatus.PROPOSED
            },
            {
                "parameter_name": "ANOMALY_DETECTION_SENSITIVITY",
                "old_value": 2.50,
                "proposed_value": 1.80,
                "change_reason": "Hassasiyet arttırılarak mikro-sapmaların daha erken yakalanması hedefleniyor.",
                "confidence_score": 0.81,
                "window_days": 21,
                "sample_size": 3100,
                "status": CalibrationStatus.REJECTED,
                "change_reason": "Red Nedeni: Çok fazla gürültü (noise) yaratma riski.",
                "approved_by": "OPERATOR_ADMIN"
            }
        ]
        
        for cal_data in calibrations:
            record = GovernorCalibrationRecord(
                id=uuid.uuid4(),
                **cal_data
            )
            db.add(record)
            
        await db.commit()
        print("[OK] 5 adet kalibrasyon kaydi eklendi.")

if __name__ == "__main__":
    asyncio.run(seed_calibrations())
