# filepath: tests/unit/test_incident_consensus_trigger.py
import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select

from libs.db.session import session_scope
from libs.db.models.core_models import OperationalIncident
from services.ui_repair.watchdog.incident_consensus_trigger import IncidentConsensusTrigger

@pytest.mark.asyncio
async def test_incident_consensus_trigger_flow():
    """
    Sistem üzerinde open ve critical seviyeli bir incident olduğunda,
    IncidentConsensusTrigger motorunun bunu otonom olarak yakaladığını,
    tartışıp çözdüğünü ve veritabanını güncellediğini doğrular.
    """
    # 1. Mock incident veritabanına ekleniyor
    mock_id = uuid.uuid4()
    async with session_scope() as session:
        incident = OperationalIncident(
            id=mock_id,
            incident_type="stuck_workflow",
            severity="critical",
            message="Kritik veri eşleme iş akışı 30 dakikadır yanıt vermiyor (Zaman Aşımı).",
            status="open",
            payload={"source": "pytest_mock"}
        )
        session.add(incident)
        await session.commit()

    # 2. Trigger tetikleniyor
    trigger = IncidentConsensusTrigger()
    reports = await trigger.scan_and_resolve_incidents()

    # 3. Sonuçların doğrulanması
    assert len(reports) >= 1
    # Find the report corresponding to our mock incident
    target_report = None
    for r in reports:
        if "Kritik veri eşleme" in r["proposal"]:
            target_report = r
            break
            
    assert target_report is not None, "Bizim eklediğimiz incident için debate raporu bulunamadı."
    assert "meeting_id" in target_report
    assert "consensus" in target_report
    assert "votes" in target_report
    assert "final_decision" in target_report

    # 4. Veritabanından incident kaydı sorgulanıyor
    async with session_scope() as session:
        stmt = select(OperationalIncident).where(OperationalIncident.id == mock_id)
        result = await session.execute(stmt)
        updated_incident = result.scalar_one()

        assert updated_incident.status == "resolved"
        assert updated_incident.resolved_at is not None
        assert "consensus_report" in updated_incident.payload
        
        saved_report = updated_incident.payload["consensus_report"]
        assert saved_report["meeting_id"] == target_report["meeting_id"]
        assert saved_report["consensus"] == target_report["consensus"]
