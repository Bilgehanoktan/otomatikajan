import pytest
import asyncio
from datetime import datetime, timezone
import uuid

# Proje YollarÄ± Config
from packages.repair_engine.memory.incident_memory import incident_memory
from packages.repair_engine.ingestion.incident_ingestor import incident_ingestor
from core.repair_orchestrator import get_repair_orchestrator
from packages.persistence.session import AsyncSessionLocal
from packages.persistence.repair_repository import RepairIncidentRepo, RepairJobRepo
from packages.persistence.repair_models import RepairIncident, RepairJobRecord

pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
async def cleanup_memory():
    """Her testten Ã¶nce ve sonra memory/ingestor temizliÄŸi"""
    incident_memory._incidents.clear()
    incident_ingestor._seen.clear()
    orch = get_repair_orchestrator()
    orch._jobs_cache.clear()
    orch._hydrated = False
    yield
    incident_memory._incidents.clear()
    incident_ingestor._seen.clear()
    orch._jobs_cache.clear()
    orch._hydrated = False

async def test_incident_memory_hydration():
    """Test: IncidentMemory veritabanÄ±ndaki aÃ§Ä±k kayÄ±tlarÄ± belleÄŸe alÄ±yor mu?"""
    # 1. DB'ye sahte (mock) veri yazalÄ±m (GerÃ§ek test DB ortamÄ± varsayÄ±mÄ±)
    test_incident_id = f"inc_test_{uuid.uuid4().hex[:8]}"
    
    async with AsyncSessionLocal() as db:
        new_record = RepairIncident(
            incident_id=test_incident_id,
            source="test_failure",
            severity="high",
            service="test_service",
            module="test_module",
            symptom="Mock error for hydration finding",
            status="open",
            first_seen_at=datetime.now(timezone.utc)
        )
        packages.persistence.add(new_record)
        await packages.persistence.commit()
        
    # 2. Hydration Metodunu Ã‡aÄŸÄ±r
    count = await incident_memory.hydrate_from_db()
    
    # 3. Ä°ddia (Assertion)
    assert count > 0, "Hydration en az 1 kayÄ±t yÃ¼klemeli"
    assert test_incident_id in incident_memory._incidents, "Eklenen test kaydÄ± hafÄ±zaya gelmeli"
    
    incident = incident_memory._incidents[test_incident_id]
    assert incident.symptom == "Mock error for hydration finding"
    assert incident.status == "open"

async def test_repair_orchestrator_hydration():
    """Test: RepairOrchestrator veritabanÄ±ndaki iÅŸleri listelerken schema sorunu Ã§Ä±kartÄ±yor mu?"""
    # 1. DB'ye Ã¶rnek onarÄ±m iÅŸi ekle
    test_incident_id = f"inc_test_{uuid.uuid4().hex[:8]}"
    test_job_id = f"rjob_test_{uuid.uuid4().hex[:8]}"
    
    async with AsyncSessionLocal() as db:
        new_inc = RepairIncident(
            incident_id=test_incident_id,
            source="test_failure", severity="high", service="test_service",
            module="test_module", symptom="Test", status="open",
            first_seen_at=datetime.now(timezone.utc)
        )
        packages.persistence.add(new_inc)
        
        new_job = RepairJobRecord(
            job_id=test_job_id,
            incident_id=test_incident_id,
            status="new",
            history=[],
            meta={"risk_score": 10, "test_field": True},  # Alembic revizyon 0008 meta alanÄ±!
            created_at=datetime.now(timezone.utc)
        )
        packages.persistence.add(new_job)
        await packages.persistence.commit()
        
    # 2. Orchestrator Hydration Ã‡aÄŸrÄ±sÄ± (Startup LifeSpan davranÄ±ÅŸÄ±)
    orch = get_repair_orchestrator()
    count = await orch.hydrate_from_db()
    
    # 3. Assertion: Alembic migrasyonu Ã§alÄ±ÅŸtÄ±ÄŸÄ± iÃ§in 'meta' Ã§Ã¶kmemeli
    assert orch._hydrated is True
    
    # 4. Liste Ã¼zerinden meta doÄŸrulama
    jobs = await orch.list_jobs(limit=100)
    found_job = next((j for j in jobs if j.job_id == test_job_id), None)
    
    assert found_job is not None, "Job listelemede gelmeli"
    assert found_job.status.value == "new"

